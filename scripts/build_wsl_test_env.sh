#!/usr/bin/env bash
# 专注学习站（focus-garden）本地测试环境：同步 → 构建 → 发布 → 重载 nginx
#
# 用法：
#   bash /srv/src/focus-garden/scripts/build_wsl_test_env.sh
#   bash /srv/src/focus-garden/scripts/build_wsl_test_env.sh --skip-build
set -euo pipefail

WIN_ROOT="${WIN_ROOT:-/mnt/c/Users/Administrator/Desktop/works/web_work}"
# /mnt/c 的文件视图会间歇性读到旧内容（变量时有时无），
# 因此本地测试环境优先用 WSL 本地固定配置 /srv/focus-garden.local.env。
ENV_FILE="${WSL_ENV_FILE:-/srv/focus-garden.local.env}"
[ -f "$ENV_FILE" ] || ENV_FILE="$WIN_ROOT/focus-garden/deploy/env/local.env"
SKIP_BUILD=0
[ "${1:-}" = "--skip-build" ] && SKIP_BUILD=1

log() { printf '\033[36m[focus]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[focus] %s\033[0m\n' "$*" >&2; exit 1; }

command -v rsync >/dev/null || die "缺少 rsync"
command -v npm >/dev/null || die "缺少 node/npm"

[ -f "$ENV_FILE" ] || die "找不到配置：$ENV_FILE"
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a
: "${FOCUS_BASE_URL:?配置里缺少 FOCUS_BASE_URL}"
: "${FOCUS_HOST:?配置里缺少 FOCUS_HOST}"
: "${BACKEND_ORIGIN:?配置里缺少 BACKEND_ORIGIN}"
: "${IDENTITY_BASE_URL:?配置里缺少 IDENTITY_BASE_URL}"
: "${IDENTITY_API_LOGIN:?配置里缺少 IDENTITY_API_LOGIN}"
: "${IDENTITY_API_SESSION:?配置里缺少 IDENTITY_API_SESSION}"
: "${IDENTITY_API_LOGOUT:?配置里缺少 IDENTITY_API_LOGOUT}"
: "${IDENTITY_PREFIX:?配置里缺少 IDENTITY_PREFIX}"
: "${IDENTITY_API_RENEW:?配置里缺少 IDENTITY_API_RENEW}"
: "${STAGE_DIR:?配置里缺少 STAGE_DIR}"

SRC="${SRC_DIR:-/srv/src}"
STAGE="$STAGE_DIR"
NAME=focus-garden

log "配置来源：$ENV_FILE"
log "站点：$FOCUS_BASE_URL"

# ---------------------------------------------------------------- 同步
mkdir -p "$SRC"
git config --global --add safe.directory "$WIN_ROOT/$NAME" 2>/dev/null || true
git config --global --add safe.directory "$WIN_ROOT/$NAME/.git" 2>/dev/null || true

if [ ! -d "$SRC/$NAME" ]; then
  log "同步 $WIN_ROOT/$NAME -> $SRC/$NAME"
  mkdir -p "$SRC/$NAME"
fi

# bash 是按字节偏移增量读取脚本的：rsync 覆盖脚本自身后，正在运行的实例
# 会读到错位的内容（表现为「脚本改了却没生效」）。
# 因此顺序必须是：先同步 → 再把自己复制到 /tmp 执行，运行中的实例就不会被换掉。
if [ -z "${FOCUS_BUILD_REEXEC:-}" ]; then
  export FOCUS_BUILD_REEXEC=1
  log "同步工作区"
  rsync -a --delete \
    --exclude '.git/' \
    --exclude 'node_modules/' \
    --exclude '.output/' \
    --exclude '.nuxt/' \
  --exclude 'scripts/build_wsl_test_env.sh' \
    "$WIN_ROOT/$NAME/" "$SRC/$NAME/"
  _self="$(mktemp /tmp/focus-build.XXXXXX.sh)"
  cp "$0" "$_self"
  exec bash "$_self" "$@"
fi

# Windows 工作区是 CRLF，统一成 LF
find "$SRC/$NAME" -type d \( -name .git -o -name node_modules -o -name .output -o -name .nuxt \) -prune -o \
  -type f \( -name '*.ts' -o -name '*.vue' -o -name '*.js' -o -name '*.mjs' \
             -o -name '*.css' -o -name '*.json' -o -name '*.md' -o -name '*.sh' \
             -o -name '*.conf' -o -name '*.html' -o -name '*.txt' -o -name '*.yml' -o -name '*.env' \) \
  -exec sed -i 's/\r$//' {} +

# ---------------------------------------------------------------- 构建
if [ "$SKIP_BUILD" -eq 0 ]; then
  cd "$SRC/$NAME"
  if [ ! -d node_modules ]; then
    log "安装依赖（npm install）"
    npm install --no-audit --no-fund
  fi
  log "构建静态站点（nuxi generate）"
  NUXT_PUBLIC_IDENTITY_BASE_URL="$IDENTITY_BASE_URL" \
  NUXT_PUBLIC_IDENTITY_API_LOGIN="$IDENTITY_API_LOGIN" \
  NUXT_PUBLIC_IDENTITY_API_SESSION="$IDENTITY_API_SESSION" \
  NUXT_PUBLIC_IDENTITY_API_LOGOUT="$IDENTITY_API_LOGOUT" \
  NUXT_PUBLIC_IDENTITY_API_RENEW="$IDENTITY_API_RENEW" \
  NUXT_PUBLIC_IDENTITY_API_GARDEN="$IDENTITY_API_GARDEN" \
  npm run generate
fi

# ---------------------------------------------------------------- 发布
log "发布 -> $STAGE/$NAME"
sudo -n mkdir -p "$STAGE/$NAME"
sudo -n rsync -a --delete "$SRC/$NAME/.output/public/" "$STAGE/$NAME/"

# ---------------------------------------------------------------- nginx
TPL="$SRC/$NAME/deploy/nginx/local.conf.template"
[ -f "$TPL" ] || die "找不到 nginx 模板：$TPL"
log "渲染 nginx -> /etc/nginx/sites-available/$NAME.conf"
sed -e "s#__FOCUS_HOST__#$FOCUS_HOST#g" \
    -e "s#__STAGE_DIR__#$STAGE#g" \
    -e "s#__FOCUS_BASE_URL__#$FOCUS_BASE_URL#g" \
    -e "s#__BACKEND_ORIGIN__#$BACKEND_ORIGIN#g" \
    -e "s#__IDENTITY_PREFIX__#$IDENTITY_PREFIX#g" \
    -e "s#__IDENTITY_API_LOGIN__#$IDENTITY_API_LOGIN#g" \
    -e "s#__IDENTITY_API_SESSION__#$IDENTITY_API_SESSION#g" \
    -e "s#__IDENTITY_API_LOGOUT__#$IDENTITY_API_LOGOUT#g" \
    -e "s#__IDENTITY_API_RENEW__#$IDENTITY_API_RENEW#g" \
    -e "s#__IDENTITY_API_GARDEN__#$IDENTITY_API_GARDEN#g" \
    "$TPL" > /tmp/$NAME.conf
NGINX_SITES_DIR="${NGINX_SITES_DIR:-/etc/nginx/sites-available}"
sudo -n install -o root -g root -m 644 /tmp/$NAME.conf "$NGINX_SITES_DIR/$NAME.conf"
sudo -n ln -sf "$NGINX_SITES_DIR/$NAME.conf" "$NGINX_SITES_DIR/../sites-enabled/$NAME.conf"

# ---------------------------------------------------------------- hosts
update_hosts() {
  local wsl_ip win_hosts
  wsl_ip=$(hostname -I | awk '{print $1}')
  log "更新 hosts（WSL IP $wsl_ip）"
  sudo -n sed -i '/# BEGIN WSL focus-garden/,/# END WSL focus-garden/d' /etc/hosts
  printf '# BEGIN WSL focus-garden\n%s %s\n# END WSL focus-garden\n' \
    "$wsl_ip" "$FOCUS_HOST" | sudo -n tee -a /etc/hosts >/dev/null

  win_hosts=/mnt/c/Windows/System32/drivers/etc/hosts
  [ -f "$win_hosts" ] || return 0
  sudo -n cp "$win_hosts" "$win_hosts.bak-focus-garden"
  {
    cat "$win_hosts" \
      | sed '/# BEGIN WSL focus-garden/,/# END WSL focus-garden/d' \
      | sed "\#^[0-9.]* $FOCUS_HOST #d"
    printf '# BEGIN WSL focus-garden\n%s %s\n# END WSL focus-garden\n' "$wsl_ip" "$FOCUS_HOST"
  } > /tmp/hosts.focus.new
  sudo -n cp /tmp/hosts.focus.new "$win_hosts"
}
update_hosts

# ---------------------------------------------------------------- 重载并自检
sudo -n nginx -t
sudo -n systemctl reload nginx

code=$(curl -sS -o /dev/null -w '%{http_code}' -H "Host: $FOCUS_HOST" http://127.0.0.1/ || true)
log "自检：$FOCUS_HOST -> HTTP $code"
log "完成。入口：$FOCUS_BASE_URL"
