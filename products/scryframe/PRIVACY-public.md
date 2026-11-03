# Scryframe privacy policy

Last updated: 3 November 2026. Applies to Scryframe 1.0.0.

## Recognition and capture

Scryframe identifies Magic cards in a video tab you explicitly activate. It
processes video pixels locally in extension-owned memory. Tab capture can include
other visible content in that tab, such as chat. Scryframe does not record or
upload gameplay frames, capture audio, or send browsing URLs to its developer.
It has no telemetry, advertising tracking or required account.

Pause suspends recognition but keeps the capture stream active. Stop ends the
capture session. Closing the preview panel or navigating away ends the session.

## Card images and local settings

Accepted matches automatically request full card images from Scryfall's image
service at cards.scryfall.io. This discloses your IP address and the requested
card to that provider. Requests omit credentials and the page referrer. Refer
to [Scryfall's privacy policy](https://scryfall.com/docs/privacy) for its handling
of requests. Scryframe does not operate a card-image proxy.

The selected format is saved locally in extension localStorage, without frames or
browsing URLs. Up to four validated card-image blobs, with a total cache-content
limit of 12 MiB, stay only in panel memory for the current session. Stop, session
changes and panel closure clear this cache. Images are not prefetched or stored
persistently. Models, matching banks, scripts and WASM are included in this version;
Scryframe does not download remote executable code.

## Permissions and control

The extension uses activeTab and scripting for the activated document, tabCapture
for video-only capture, offscreen for the extension-owned processing document and
sidePanel for previews and controls. It does not request permanent access to all
websites, browser history, cookies or filesystem access. Some pages, protected
content and embedded players cannot be accessed.

You can stop a session, disable or uninstall Scryframe in your browser. Your
browser manages removal of extension-local data. Browser/store services have
their own privacy practices independently of Scryframe.

## Optional financial support

The “Support development” link opens Yureeh / Strixia’s Ko-fi page only when you
choose to click it. No Ko-fi scripts, widgets, tracking pixels or payment forms
are embedded in Scryframe. The extension does not receive payment details or
supporter identities, and contributions do not unlock features. Ko-fi and your
chosen payment provider handle their own pages and transactions under their
privacy policies: [Ko-fi privacy](https://more.ko-fi.com/privacy).

## Voluntary support and rights requests

Contact yureefabbri@gmail.com for private support or rights/removal requests.
You may also deliberately submit a public GitHub issue. Do not include private
URLs, screenshots, credentials or personal information in public reports. No
automatic diagnostic upload is performed. Information you choose to send is used
to investigate and respond to your request; public issue content is visible to others.

## Changes

Review this policy when updating Scryframe. Changes to capture, storage, networking
or permissions must be reflected here and in the corresponding store disclosures.
