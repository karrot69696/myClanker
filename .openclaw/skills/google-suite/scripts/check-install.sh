#!/bin/bash
# check if gogcli is installed and authenticated

if ! command -v gog &> /dev/null; then
    echo "❌ gogcli not installed"
    echo ""
    echo "install via:"
    echo "  brew install gogcli"
    echo ""
    echo "or build from source:"
    echo "  git clone https://github.com/steipete/gogcli.git"
    echo "  cd gogcli && make && sudo cp bin/gog /usr/local/bin/"
    exit 1
fi

echo "✅ gogcli installed: $(gog --version)"

# check if any accounts are configured
if gog auth list 2>&1 | grep -q "No accounts"; then
    echo "⚠️  no accounts configured"
    echo ""
    echo "setup OAuth:"
    echo "  1. create OAuth client in Google Cloud Console"
    echo "  2. download client JSON"
    echo "  3. gog auth credentials ~/Downloads/client_secret_....json"
    echo "  4. gog auth add your@gmail.com"
    exit 2
fi

echo "✅ accounts configured:"
gog auth list

exit 0
