# Nucleus Deck — experimental SteamOS edition

This is a **Linux-native** entry point for the Nucleus Co-op fork, **not** the original Windows .NET/WinForms program running under Wine. SteamOS does not need Windows installed. For game launching it integrates the existing, Linux-native [PartyDeck](https://github.com/partydeck/partydeck) runtime rather than pretending the Windows-only Nucleus hooking engine can be rebuilt for Linux.

**Status:** early integration / test on a real Steam Deck still required. The launcher, installer, dependency diagnostics, SHA256-verified runtime downloads and desktop shortcut are implemented. **Nucleus .js handlers are not compatible**, and no claim is made that all existing Nucleus games work. The two-player World at War procedure below uses a separate **PartyDeck .pd2 handler**.

## Requirements

- Steam Deck on SteamOS **3.7+**, Desktop Mode (KDE Plasma 6); a dock/TV is optional.
- Two independently recognized controllers, or Deck controls plus one controller.
- An owned, installed copy of World at War and any other necessary game files; no games are distributed here.
- Available storage for separate game profiles/Proton prefixes.
- Network connection for initial downloads and game/launcher setup.
- SteamOS-bundled **gamescope**, **bubblewrap**, Python 3 and KDE **kdialog**.
- PartyDeck and, for Windows games, a configured Proton/UMU runtime. PartyDeck can download additional runtime dependencies separately.

## Download a prepackaged launcher

Instead of checking out the source, download the **nucleus-deck-steamos** artifact from the newest successful [SteamOS native launcher checks workflow](https://github.com/GiantDwarf288/splitscreenme-nucleus/actions/workflows/steamos-native.yml) on this branch (GitHub sign-in may be required). Unzip the GitHub artifact to obtain `nucleus-deck-steamos.tar.gz`, then in Konsole:

```bash
cd ~/Downloads
tar -xzf nucleus-deck-steamos.tar.gz
bash nucleus-deck/install.sh
~/.local/bin/nucleus-deck --doctor
```

This small artifact contains the **native launcher only**. The first-time **Install/update SteamOS runtime** action downloads the official PartyDeck SteamOS runtime separately.

## Install into your home directory (no sudo / Windows)

In Steam Deck Desktop Mode, open Konsole:

```bash
cd ~
git clone --depth 1 --filter=blob:none --sparse --branch feature/steamos-native-deck-edition \
  https://github.com/GiantDwarf288/splitscreenme-nucleus.git nucleus-deck-source
cd nucleus-deck-source
git sparse-checkout set steamdeck
bash steamdeck/install.sh
~/.local/bin/nucleus-deck --doctor
```

Then open **Nucleus Deck (SteamOS)** from the Applications menu. Select **Install/update SteamOS runtime**. The installer fetches PartyDeck's **latest official SteamOS x86_64 tarball**, verifies the release-provided SHA256 digest and extracts it under `~/.local/share/nucleus-deck/partydeck/`. The installer refuses symlinks/traversal paths inside archives and does **not** change system partitions or use root.

Select **Start split-screen launcher** to open PartyDeck. If automatic tiling or controller separation fails, check SteamOS updates, Gamescope, Bubblewrap and your Steam Input configuration. The launcher itself is not a replacement for PartyDeck's configuration interface.

CLI equivalents:

```bash
~/.local/bin/nucleus-deck --doctor
~/.local/bin/nucleus-deck --install-backend
~/.local/bin/nucleus-deck --launch
~/.local/bin/nucleus-deck --handler-guide
```

## World at War Zombies — two players

1. Install **World at War** from an owned copy. Install [Plutonium](https://www.plutonium.pw/docs/) if using the Plutonium-based launcher.
2. Download the latest official [Call of Duty Alt Launcher](https://github.com/framilano/CallofDutyAltLauncher/releases) and extract it to a directory you can find.
3. Read the game handler author's [PartyDeck issue #190](https://github.com/partydeck/partydeck/issues/190). Download the **PartyDeck .pd2 handler linked in that issue**, and import it into PartyDeck with its import button. **Do not use a Nucleus .js handler**.
4. Set up **two persistent profiles / separate WOW64 Proton prefixes** in PartyDeck, and select Proton-GE or a supported Proton Experimental version as described by the handler author. Assign one physical controller to each player. If using Deck controls, ensure they aren't simultaneously presented as multiple virtual devices. Disable Steam Input for the PartyDeck shortcut when running in Gaming Mode, as advised by PartyDeck.
5. Point both player profiles to Call of Duty Alt Launcher and configure each instance's paths to Plutonium and your installed WaW game. The handler author advises installing the `xact` component for WaW audio **in each profile's prefix** using winetricks. Set up the appropriate runtime first; do not run global Wine commands against your Steam prefix.
6. Launch **offline WaW** in both instances, open the in-game console for Player 1 and enter `sp_minplayers 2`. Start the Zombies match. In Player 2's console enter `connect localhost:28960` to join the locally hosted match.

These console commands come from the [handler author](https://github.com/partydeck/partydeck/issues/190), who also documents offline and online support, setup steps and known issues. The procedure is **not yet device-tested in this fork**; game updates and Plutonium behavior can affect it.

### Playing through Steam Gaming Mode

PartyDeck's SteamOS distribution includes `GamingModeLauncher.sh`. For Gaming Mode, add **that PartyDeck script**, not the Nucleus Deck desktop shortcut, as a non-Steam game in Steam, and disable Steam Input for that shortcut per [PartyDeck's instructions](https://github.com/partydeck/partydeck). The desktop shortcut launches the normal KDE application.

### Diagnostics and boundaries

- The new frontend is Python 3 standard-library code and KDE dialogs, so **no Windows executable or .NET Framework** is required for the frontend.
- Windows game executables still run **through Proton inside PartyDeck**. That's not installing Windows.
- Steam game compatibility, DRM, controller enumeration and game networking remain per-game concerns. This integration does not defeat DRM or supply bypassed game files.
- Backend releases are obtained from official GitHub releases with SHA256 validation, but third-party handler packages and external launchers must be reviewed separately.
- SteamOS is immutable by default; everything here installs to the user home directory.
- Running two game instances has a performance cost. On an undocked Deck at 1280×800, test the horizontal split and low per-instance graphics settings first.
- Nucleus upstream remains Windows-only and untouched. Linux handler parity is **not implemented** in this phase.

Run tests from the repository root:

```bash
python3 -m unittest discover -s steamdeck/tests -v
bash -n steamdeck/install.sh
```

## Attribution

Nucleus Co-op is GPL-3.0; see the repository license and upstream credits. PartyDeck and Call of Duty Alt Launcher are independent third-party projects, not bundled or re-licensed by this fork. This experimental integration downloads PartyDeck's published Linux release when explicitly requested.
