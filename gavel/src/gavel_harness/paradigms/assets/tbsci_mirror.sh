
RUN (sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g; s|http://archive.ubuntu.com|http://mirrors.aliyun.com|g; s|http://security.ubuntu.com|http://mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null; sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g; s|http://archive.ubuntu.com|http://mirrors.aliyun.com|g; s|http://security.ubuntu.com|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/*.sources 2>/dev/null; true)
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV HF_ENDPOINT=https://hf-mirror.com
