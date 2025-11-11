# Home Assistant integration for Qustodio

[Qustodio](https://www.qustodio.com) is a parental control infrastructure, it can control multiple devices (among which iOS, Android, Windows, Mac) for multiple kids, with many useful features. As a parent, I have yet to find a better parental control tool.

This integration allows you to integrate _Qustodio_ features into [Home Assistant](https://www.home-assistant.io). It is not cracking, no copyright infringement, there is no specific rights that this integration would give you that you would not have with the _Qustodio_ app or website. Just an alternative way to deal with parental control.

A [Qustodio](https://www.qustodio.com) account is needed for this to work at all.

## Disclaimer

I (Willow) am not the primary author of this integration. I have forked <https://github.com/benmac7/qustodio>, which itself is a rewrite by _Claude_ of <https://github.com/dotKrad/hass-qustodio>.

I also am not affiliated at all with _Qustodio_, apart from being a proud mother of two, using this tool to deal with my kids' obsession with screens. I don't receive any money or compensation from anyone, this work is 100% benevolent.

You must be aware that this is customization things, not official from _Home Assistant_, not officially endorsed by anyone, blah blah usual disclaimer, I'm not responsible if your kids get unlimited time because of a wrong configuration, or if you block anything you did not want to block, if a pink unicorn appears in your garden, or any other inconvenience... but of course I will gladly accept any feedback, bug report, feature request, etc.

## Installation

### Prerequisite

You must have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.

### Installing the integration

- Click on this link: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=willoma&repository=qustodio-ha&category=integration)

- Validate opening the link in your Home Assistant instance
- Click on the "Add" button in the popup (which will configure HACS to take this integration into account)
- Click on "Download" in the bottom right corner (which will install the integration)
- Restart Home Assistant (see in the _Settings_ section)

### Connecting to your Qustodio account

- Go to _Settings_ → _Devices & services_
- Click on _Add integration_ in the bottom right corner
- Select _Qustodio_ in the list
- Enter your Qustodio login (email) and password in the "Qustodio Setup" popup
- If they are correct, your kids will be detected and a device will be created in Home Assistant for each of them.
