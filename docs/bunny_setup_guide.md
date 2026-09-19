# Bunny Account Setup Guide (New Free Trial)

Follow every step in order. At the end, you'll have all `.env` values ready.

---

## Step 1: Create Bunny Account

1. Go to [https://dash.bunny.net/auth/register](https://dash.bunny.net/auth/register)
2. Sign up with email → verify → login to dashboard

---

## Step 2: Get Your Account API Key

1. Dashboard → Click your **profile icon** (top-right) → **Account Settings**
2. Scroll to **API Key** section → Copy the key

```env
BUNNY_STREAM_API_KEY=<paste here>
```

---

## Step 3: Create a Video Library (Bunny Stream)

1. Dashboard → **Stream** (left sidebar) → **Add Video Library**
2. Give it a name (e.g., `TalentSea`)
3. Select a **Tier** (Standard is fine for free trial)
4. Choose nearest **Replication Region**
5. Click **Add Video Library**

### After creation, get the Library ID:
- You'll be inside the library → Look at the URL: `https://dash.bunny.net/stream/{LIBRARY_ID}`
- OR go to **Library Settings** → the Library ID is shown at the top

```env
BUNNY_STREAM_LIBRARY_ID=<paste the number>
```

---

## Step 4: Enable Token Authentication (Stream)

1. Inside your Stream Library → **Security** tab
2. Toggle **Token Authentication** → **ON**
3. Copy the **Token Authentication Key** shown

```env
BUNNY_STREAM_TOKEN_KEY=<paste the key>
```

> [!IMPORTANT]
> This is the key used in `SHA256(token_key + video_id + expires)`. Copy it exactly.

---

## Step 5: Get the Stream Pull Zone URL

1. Inside your Stream Library → **Delivery** tab (or **Settings**)
2. Look for the **CDN Hostname** / **Pull Zone URL** — it looks like `vz-xxxxxxxx-xxx.b-cdn.net`

```env
BUNNY_PULL_ZONE_URL=https://vz-xxxxxxxx-xxx.b-cdn.net
```

### ⚠️ Verify CDN Pull Zone Token Auth is OFF
1. Dashboard → **CDN** (left sidebar) → Find the auto-created pull zone (same `vz-` name)
2. Click it → **Security** tab
3. Make sure **Token Authentication** is **OFF** here
4. Stream's own token auth handles security — CDN pull zone token auth must stay OFF

---

## Step 6: Create a Storage Zone (for thumbnails, avatars, banners)

1. Dashboard → **Storage** (left sidebar) → **Add Storage Zone**
2. Name it (e.g., `talent-sea-storage`)
3. Select **Standard** tier, pick nearest region
4. Click **Add Storage Zone**

### Get the credentials:
- Inside the storage zone → **FTP & API Access**
- Copy the **Password** and **Zone Name**

```env
BUNNY_STORAGE_ZONE_NAME=talent-sea-storage
BUNNY_STORAGE_PASSWORD=<paste the storage API password>
```

---

## Step 7: Create a Pull Zone for Storage (for public image CDN delivery)

1. Dashboard → **CDN** → **Add Pull Zone**
2. Name it (e.g., `talent-sea-storage-cdn`)
3. **Origin Type** → Select **Storage Zone** → Pick the storage zone you just created
4. Click **Add Pull Zone**

### Get the hostname:
- Inside the pull zone → Copy the **Hostname** (e.g., `talent-sea-storage-cdn.b-cdn.net`)

```env
BUNNY_STORAGE_PULL_ZONE_URL=https://talent-sea-storage-cdn.b-cdn.net
```

### Make sure Token Auth is OFF on this pull zone
- This serves public thumbnails/avatars — no auth needed

---

## Step 8: Upload a Test Video

1. Dashboard → **Stream** → Your Library → **Upload**
2. Upload any short test video
3. Wait for transcoding to finish (status becomes green/ready)
4. Copy the **Video ID** (UUID like `0b14de6f-621a-404d-bf58-5ae6c74f5e03`)
5. Test in browser: open the **Embed View** tab → video should play in the iframe preview

---

## Step 9: Update `.env` on Your Server

SSH into your server and update all 6 Bunny variables:

```env
# Bunny Stream API Credentials
BUNNY_STREAM_API_KEY=<from Step 2>
BUNNY_STREAM_LIBRARY_ID=<from Step 3>
BUNNY_STREAM_TOKEN_KEY=<from Step 4>

# Bunny Storage API Credentials
BUNNY_STORAGE_PASSWORD=<from Step 6>
BUNNY_STORAGE_ZONE_NAME=<from Step 6>

# Bunny CDN Pull Zone URLs
BUNNY_PULL_ZONE_URL=https://vz-xxxxxxxx-xxx.b-cdn.net  # from Step 5
BUNNY_STORAGE_PULL_ZONE_URL=https://your-storage-cdn.b-cdn.net  # from Step 7
```

---

## Step 10: Restart the Server

```bash
cd /home/madhu/content-talent-backend
git pull
# Kill old server process, then:
nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

---

## Final Checklist

| Setting | Value |
|---|---|
| Stream Library Token Auth | ✅ ON |
| CDN Pull Zone Token Auth (stream) | ❌ OFF |
| CDN Pull Zone Token Auth (storage) | ❌ OFF |
| `.env` BUNNY_STREAM_TOKEN_KEY | Matches Stream Library Security key |
| Code formula | `SHA256(key + video_id + expires)` |
