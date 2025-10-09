# yomite

Local OCR helper, primarily intended for reading visual novels in Japanese.

## Installation

### NixOS

```
nix profile install github:ElnuDev/yomite
```

You can then run `yomite` from the command line or from your run menu.

### Other Linux

First, install `python3` and [`tesseract`](https://github.com/tesseract-ocr/tesseract) using your distro's package manager.

yomite uses a different area selection tool depending on what display server you're using. If you are on Wayland, install [`slurp`](https://github.com/emersion/slurp). If you are on X11, install [`slop`](https://github.com/naelstrof/slop). If you aren't sure what display server you're using, you can find out using the command `echo $XDG_SESSION_TYPE`.

You can then clone the repository.

```
git clone https://github.com/ElnuDev/yomite.git
cd yomite
pip install -r requirements.txt
python src
```

## License

yomite is licensed under the [GNU General Public License v3.0](LICENSE.md). The power icon is from [heroicons](https://github.com/tailwindlabs/heroicons) under the MIT license.