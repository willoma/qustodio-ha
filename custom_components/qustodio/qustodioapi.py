"""Qustodio API client."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, date
from typing import Any

import aiohttp
import async_timeout

from .const import LOGIN_RESULT_OK, LOGIN_RESULT_UNAUTHORIZED, LOGIN_RESULT_ERROR

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 15

# Qustodio API URLs - these are based on reverse engineering and may change
URL_LOGIN = "https://api.qustodio.com/v1/oauth2/access_token"
URL_ACCOUNT = "https://api.qustodio.com/v1/accounts/me"
URL_PROFILES = "https://api.qustodio.com/v1/accounts/{}/profiles/"
URL_RULES = "https://api.qustodio.com/v1/accounts/{}/profiles/{}/rules?app_rules=1"
URL_DEVICES = "https://api.qustodio.com/v1/accounts/{}/devices"
URL_HOURLY_SUMMARY = "https://api.qustodio.com/v2/accounts/{}/profiles/{}/summary_hourly?date={}"
URL_ACTIVITY = "https://api.qustodio.com/v1/accounts/{}/profiles/{}/activity"

# Client credentials - these are extracted from the mobile app and may change
CLIENT_ID = "264ca1d226906aa08b03"
CLIENT_SECRET = "3e8826cbed3b996f8b206c7d6a4b2321529bc6bd"


class QustodioApi:
    """Qustodio API client."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._session = None
        self._access_token = None
        self._expires_in = None
        self._account_id = None
        self._account_uid = None

    async def login(self) -> str:
        """Login to Qustodio API."""
        if (
            self._access_token is not None
            and self._expires_in is not None
            and self._expires_in > datetime.now()
        ):
            return LOGIN_RESULT_OK

        _LOGGER.debug("Logging in to Qustodio API")
        
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=TIMEOUT),
                headers={"User-Agent": "Qustodio/2.0.0 (Android)"}
            ) as session:
                async with session.post(URL_LOGIN, data=data) as response:
                    if response.status == 401:
                        _LOGGER.error("Unauthorized: Invalid credentials")
                        return LOGIN_RESULT_UNAUTHORIZED

                    if response.status != 200:
                        text = await response.text()
                        _LOGGER.error("Login failed with status %s: %s", response.status, text)
                        return LOGIN_RESULT_ERROR

                    response_data = await response.json()
                    
                    if "access_token" not in response_data:
                        _LOGGER.error("No access token in response")
                        return LOGIN_RESULT_ERROR
                    
                    self._access_token = response_data["access_token"]
                    self._expires_in = datetime.now() + timedelta(
                        seconds=response_data.get("expires_in", 3600)
                    )
                    _LOGGER.debug("Login successful")
                    return LOGIN_RESULT_OK

        except asyncio.TimeoutError:
            _LOGGER.error("Login timeout")
            return LOGIN_RESULT_ERROR
        except aiohttp.ClientError as err:
            _LOGGER.error("Login connection error: %s", err)
            return LOGIN_RESULT_ERROR
        except Exception as err:
            _LOGGER.error("Login error: %s", err)
            return LOGIN_RESULT_ERROR

    async def get_data(self) -> dict[str, Any]:
        """Get data from Qustodio API."""
        _LOGGER.debug("Getting data from Qustodio API")
        data = {}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=TIMEOUT),
                headers={"User-Agent": "Qustodio/2.0.0 (Android)"}
            ) as session:
                self._session = session
                
                if await self.login() != LOGIN_RESULT_OK:
                    return data

                headers = {
                    "Authorization": f"Bearer {self._access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }

                # Get account info
                async with session.get(URL_ACCOUNT, headers=headers) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to get account info: %s", response.status)
                        return data

                    account_data = await response.json()
                    self._account_id = account_data["id"]
                    self._account_uid = account_data.get("uid", account_data["id"])

                # Get devices
                _LOGGER.debug("Getting devices")
                devices = {}
                try:
                    async with session.get(
                        URL_DEVICES.format(self._account_id), headers=headers
                    ) as response:
                        if response.status == 200:
                            devices_data = await response.json()
                            devices = {device["id"]: device for device in devices_data}
                        else:
                            _LOGGER.warning("Failed to get devices: %s", response.status)
                except Exception as err:
                    _LOGGER.warning("Error getting devices: %s", err)

                # Get profiles
                _LOGGER.debug("Getting profiles")
                async with session.get(
                    URL_PROFILES.format(self._account_id), headers=headers
                ) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to get profiles: %s", response.status)
                        return data

                    profiles_data = await response.json()

                days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                dow = days[datetime.today().weekday()]

                for profile in profiles_data:
                    _LOGGER.debug("Processing profile: %s", profile["name"])
                    profile_data = {
                        "id": profile["id"],
                        "uid": profile.get("uid", profile["id"]),
                        "name": profile["name"],
                        "is_online": profile.get("status", {}).get("is_online", False),
                        "unauthorized_remove": False,
                        "device_tampered": None,
                    }

                    # Check for unauthorized device removal
                    device_ids = profile.get("device_ids", [])
                    for device_id in device_ids:
                        if device_id in devices:
                            device = devices[device_id]
                            alerts = device.get("alerts", {})
                            if alerts.get("unauthorized_remove", False):
                                profile_data["unauthorized_remove"] = True
                                profile_data["device_tampered"] = device.get("name", "Unknown")

                    # Set current device and location
                    status = profile.get("status", {})
                    location = status.get("location", {})
                    device_id = location.get("device")
                    
                    if profile_data["is_online"] and device_id and device_id in devices:
                        profile_data["current_device"] = devices[device_id].get("name")
                    else:
                        profile_data["current_device"] = None

                    profile_data["latitude"] = location.get("latitude")
                    profile_data["longitude"] = location.get("longitude")
                    profile_data["accuracy"] = location.get("accuracy", 0)
                    profile_data["lastseen"] = status.get("lastseen")

                    # Get rules for quota
                    profile_data["quota"] = 0
                    try:
                        async with session.get(
                            URL_RULES.format(self._account_id, profile_data["id"]),
                            headers=headers,
                        ) as response:
                            if response.status == 200:
                                rules_data = await response.json()
                                time_restrictions = rules_data.get("time_restrictions", {})
                                quotas = time_restrictions.get("quotas", {})
                                profile_data["quota"] = quotas.get(dow, 0)
                            else:
                                _LOGGER.debug("No rules found for profile %s", profile["name"])
                    except Exception as err:
                        _LOGGER.warning("Failed to get rules for profile %s: %s", profile["name"], err)

                    # Get screen time data
                    profile_data["time"] = 0
                    try:
                        # Try hourly summary first
                        async with session.get(
                            URL_HOURLY_SUMMARY.format(
                                self._account_uid, profile_data["uid"], date.today()
                            ),
                            headers=headers,
                        ) as response:
                            if response.status == 200:
                                hourly_data = await response.json()
                                total_time = sum(
                                    entry.get("screen_time_seconds", 0) 
                                    for entry in hourly_data
                                )
                                profile_data["time"] = round(total_time / 60, 1)  # Convert to minutes
                            else:
                                _LOGGER.debug("Hourly summary not available for profile %s", profile["name"])
                    except Exception as err:
                        _LOGGER.warning("Failed to get screen time for profile %s: %s", profile["name"], err)

                    data[profile_data["id"]] = profile_data

                self._session = None
                return data

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting data from Qustodio API")
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error getting data from Qustodio API: %s", err)
        except Exception as err:
            _LOGGER.error("Error getting data from Qustodio API: %s", err)
        finally:
            self._session = None
            
        return data