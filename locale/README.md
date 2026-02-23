# SC-Controller Translations

Currently available:
- **pt_BR** (Português do Brasil) - Complete (2432 strings)

## Adding New Languages

To add a new language:

1. Create directory structure:
   ```bash
   mkdir -p locale/LANG_CODE/LC_MESSAGES
   ```

2. Copy and translate the .po file:
   ```bash
   cp locale/pt_BR/LC_MESSAGES/sc-controller.po \
      locale/LANG_CODE/LC_MESSAGES/sc-controller.po
   # Edit the .po file with translations
   ```

3. Compile to .mo:
   ```bash
   msgfmt locale/LANG_CODE/LC_MESSAGES/sc-controller.po \
          -o locale/LANG_CODE/LC_MESSAGES/sc-controller.mo
   ```

4. Update setup.py to include the new locale:
   ```python
   ("share/locale/LANG_CODE/LC_MESSAGES", 
    ["locale/LANG_CODE/LC_MESSAGES/sc-controller.mo"]),
   ```

5. Test:
   ```bash
   LANGUAGE=LANG_CODE python -m scc.bin.sc_controller
   ```

Example language codes: de_DE, fr_FR, es_ES, it_IT, ru_RU, ja_JP

## Translation Status

| Language | Strings | Status |
|----------|---------|--------|
| pt_BR    | 2432    | ✅ Complete |

## Contributing

If you'd like to contribute translations, please:
1. Create the .po file for your language
2. Submit via GitHub pull request
3. Or email the translated .po file

## Version 0.5.5 Features

This version includes support for:
- DualSense (PS5) controllers
- All standard Steam Controller features
- Full Brazilian Portuguese translation
