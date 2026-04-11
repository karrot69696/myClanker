FROM mcr.microsoft.com/playwright/python:v1.43.0

RUN apt-get update && apt-get install -y \
    git curl ca-certificates gnupg \
    tesseract-ocr tesseract-ocr-eng \
    ffmpeg \
    jq \
    ripgrep \
    poppler-utils \
    ghostscript \
    qpdf \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages \
    pymupdf pytesseract pillow \
    requests beautifulsoup4 pandas \
    faster-whisper ocrmypdf pdfplumber semgrep

RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp && chmod a+rx /usr/local/bin/yt-dlp

RUN npm config set fetch-retries 5 \
    && npm config set fetch-retry-factor 2 \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm config set registry https://registry.npmjs.org/

RUN for i in 1 2 3; do npm install -g --no-audit --no-fund openclaw@latest && break; if [ "$i" -eq 3 ]; then exit 1; fi; npm cache clean --force; sleep 10; done

RUN for i in 1 2 3; do npm install -g --no-audit --no-fund playwright && break; if [ "$i" -eq 3 ]; then exit 1; fi; npm cache clean --force; sleep 10; done \
    && node $(npm root -g)/playwright/cli.js install chromium --with-deps

RUN mkdir -p /opt/ast-grep \
    && for i in 1 2 3; do npm install --prefix /opt/ast-grep --no-audit --no-fund @ast-grep/cli && break; if [ "$i" -eq 3 ]; then exit 1; fi; npm cache clean --force; sleep 10; done \
    && ln -sf /opt/ast-grep/node_modules/.bin/sg /usr/local/bin/ast-grep

WORKDIR /root/.openclaw
EXPOSE 18791

CMD sh -c "\
    node -e \"const fs=require('fs'); const p='/root/.openclaw/openclaw.json'; if(fs.existsSync(p)){ const c=JSON.parse(fs.readFileSync(p,'utf8')); c.tools=Object.assign({}, c.tools, {profile:'full', exec:{host:'gateway', security:'full', ask:'off'}}); c.gateway=Object.assign({}, c.gateway, {port:18791, bind:'custom', customBindHost:'0.0.0.0'}); fs.writeFileSync(p, JSON.stringify(c, null, 2)); }\" \
    && (while true; do sleep 5; openclaw devices approve --latest 2>/dev/null || true; done) \
    & openclaw gateway run"
