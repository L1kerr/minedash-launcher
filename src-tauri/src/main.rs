// MineDash Launcher — Tauri (Rust) backend.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use base64::Engine;
use serde::{Deserialize, Serialize};
use sha1::{Digest, Sha1};
use sha2::Sha256;
use tauri::{AppHandle, Emitter, Manager, State, WindowEvent};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_shell::ShellExt;

// ─────────────────────────────────────────────────────────── types

#[derive(Serialize, Deserialize, Clone, Default)]
pub struct Settings {
    pub nickname: String,
    #[serde(default = "default_auth_url")]
    pub authUrl: String,
    #[serde(default = "default_bg")]
    pub backgroundId: String,
    #[serde(default = "default_scene")]
    pub scene: String,
    /// Пользовательская тема (Workshop): если задана — используется вместо палитры категории.
    #[serde(default)]
    pub userTheme: Option<UserTheme>,
    pub javaPath: Option<String>,
    #[serde(default = "default_mem")]
    pub memoryMb: u32,
    #[serde(default)]
    pub jvmArgs: String,
    #[serde(default = "default_rw")]
    pub resolutionW: u32,
    #[serde(default = "default_rh")]
    pub resolutionH: u32,
    #[serde(default)]
    pub fullscreen: bool,
    #[serde(default = "default_server")]
    pub serverAddress: String,
    #[serde(default = "default_true")]
    pub autoJoin: bool,
    #[serde(default)]
    pub closeOnPlay: bool,
}

fn default_auth_url() -> String { "https://minedash.fun".into() }
fn default_bg() -> String { "b:space.png".into() }
fn default_scene() -> String { "heli".into() }
fn default_mem() -> u32 { 4096 }
fn default_rw() -> u32 { 1920 }
fn default_rh() -> u32 { 1080 }
fn default_server() -> String { "mc.minedash.fun".into() }
fn default_true() -> bool { true }

/// Санитайзер: старые/битые значения (0, пустые) заменяются дефолтами.
fn sanitize_settings(s: &mut Settings) {
    if s.memoryMb == 0 {
        s.memoryMb = default_mem();
    }
    if s.resolutionW == 0 {
        s.resolutionW = default_rw();
    }
    if s.resolutionH == 0 {
        s.resolutionH = default_rh();
    }
    if s.serverAddress.trim().is_empty() {
        s.serverAddress = default_server();
    }
    if s.authUrl.trim().is_empty() || s.authUrl.contains("127.0.0.1") || s.authUrl.contains("localhost") || s.authUrl.contains("api.minedash.fun") {
        s.authUrl = default_auth_url();
    }
    if s.scene.is_empty() {
        s.scene = default_scene();
    }
}

#[derive(Serialize, Deserialize, Clone, Default)]
pub struct AuthState {
    pub token: String,
    pub nick: String,
    pub uuid: String,
}

#[derive(Serialize, Deserialize, Clone, Default)]
pub struct Skin {
    pub model: String,
    pub file: Option<String>,
}

#[derive(Serialize, Deserialize, Clone, Default)]
pub struct StoreShape {
    pub settings: Settings,
    pub skin: Option<Skin>,
    #[serde(default)]
    pub backgrounds: Vec<BgRef>,
    #[serde(default = "default_version")]
    pub lastVersion: String,
    #[serde(default = "default_server_id")]
    pub lastServer: String,
    pub auth: Option<AuthState>,
}

fn default_version() -> String { "1.21.1".into() }
fn default_server_id() -> String { "create".into() }

#[derive(Serialize, Deserialize, Clone, Default)]
pub struct UserTheme {
    pub name: String,
    pub author: String,
    /// Фон лаунчера (id из списка фонов), если тема несёт свой фон.
    #[serde(default)]
    pub bgId: Option<String>,
    pub bg: String,
    pub panel: String,
    pub panel2: String,
    pub line: String,
    pub line2: String,
    pub line3: String,
    pub chip: String,
    pub chipHover: String,
    pub accent: String,
    pub accentHover: String,
    pub accentSoft: String,
    pub cyan: String,
}

impl UserTheme {
    /// Файл формата .mdstyle — JSON с палитрой + опциональным фоном (png, внедрён как base64).
    fn to_mdstyle(&self, bg_png: Option<Vec<u8>>) -> String {
        #[derive(Serialize)]
        struct MdStyle<'a> {
            format: u32,
            name: &'a str,
            author: &'a str,
            colors: Vec<(&'a str, &'a str)>,
            background: Option<String>,
        }
        let colors = vec![
            ("bg", self.bg.as_str()), ("panel", self.panel.as_str()), ("panel2", self.panel2.as_str()),
            ("line", self.line.as_str()), ("line2", self.line2.as_str()), ("line3", self.line3.as_str()),
            ("chip", self.chip.as_str()), ("chipHover", self.chipHover.as_str()),
            ("accent", self.accent.as_str()), ("accentHover", self.accentHover.as_str()),
            ("accentSoft", self.accentSoft.as_str()), ("cyan", self.cyan.as_str()),
        ];
        let background = bg_png.map(|b| format!("data:image/png;base64,{}", base64::engine::general_purpose::STANDARD.encode(b)));
        serde_json::to_string_pretty(&MdStyle {
            format: 1,
            name: &self.name,
            author: &self.author,
            colors,
            background,
        })
        .unwrap()
    }

    fn from_mdstyle(raw: &str) -> Result<(UserTheme, Option<Vec<u8>>), String> {
        #[derive(Deserialize)]
        struct MdStyle {
            name: Option<String>,
            author: Option<String>,
            colors: Option<std::collections::HashMap<String, String>>,
            background: Option<String>,
        }
        let v: MdStyle = serde_json::from_str(raw).map_err(|e| e.to_string())?;
        let c = v.colors.unwrap_or_default();
        let get = |k: &str| c.get(k).cloned().unwrap_or_default();
        let bg_png = v.background.and_then(|data| {
            let b64 = data.split(',').nth(1)?.to_string();
            base64::engine::general_purpose::STANDARD.decode(b64).ok()
        });
        Ok((
            UserTheme {
                name: v.name.unwrap_or_else(|| "Моя тема".into()),
                author: v.author.unwrap_or_else(|| "неизвестный".into()),
                bgId: None,
                bg: get("bg"), panel: get("panel"), panel2: get("panel2"),
                line: get("line"), line2: get("line2"), line3: get("line3"),
                chip: get("chip"), chipHover: get("chipHover"),
                accent: get("accent"), accentHover: get("accentHover"),
                accentSoft: get("accentSoft"), cyan: get("cyan"),
            },
            bg_png,
        ))
    }
}

#[derive(Serialize, Deserialize, Clone)]
pub struct BgRef {
    pub id: String,
    pub name: String,
    pub file: String,
}

#[derive(Serialize, Clone)]
pub struct BackgroundMeta {
    pub id: String,
    pub name: String,
    pub file: String,
    pub builtin: bool,
    pub category: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct SkinPayload {
    pngBase64: String,
    model: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct ProgressState {
    pub stage: String,
    #[serde(default)]
    pub file: Option<String>,
    pub done: u64,
    pub total: u64,
    pub speed: u64,
}

#[derive(Serialize, Clone)]
pub struct LaunchResult {
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

// ─────────────────────────────────────────────────────────── store

struct AppState {
    store: Mutex<StoreShape>,
    game_running: Mutex<bool>,
}

fn store_file(app: &AppHandle) -> PathBuf {
    let dir = app.path().app_data_dir().expect("app dir");
    dir.join("launcher.json")
}

const DEFAULT_SKIN_BYTES: &[u8] = include_bytes!("../../resources/skins/default.png");
const BUILTIN_BACKGROUNDS_ZIP: &[u8] = include_bytes!("../../resources/backgrounds.zip");

fn extract_builtin_resources(app: &AppHandle) {
    let bg_dir = user_bg_dir(app);
    let _ = fs::create_dir_all(&bg_dir);
    let count = fs::read_dir(&bg_dir)
        .map(|entries| entries.filter_map(|e| e.ok()).count())
        .unwrap_or(0);
    if count < 10 {
        let cursor = std::io::Cursor::new(BUILTIN_BACKGROUNDS_ZIP);
        if let Ok(mut archive) = zip::ZipArchive::new(cursor) {
            for i in 0..archive.len() {
                if let Ok(mut entry) = archive.by_index(i) {
                    if entry.is_dir() {
                        continue;
                    }
                    let name = entry.name().to_string();
                    if name.contains("..") || name.starts_with('/') || name.starts_with('\\') {
                        continue;
                    }
                    let out_path = bg_dir.join(&name);
                    if let Ok(mut out) = fs::File::create(&out_path) {
                        let _ = std::io::copy(&mut entry, &mut out);
                    }
                }
            }
        }
    }

    let s_dir = skins_dir(app);
    let _ = fs::create_dir_all(&s_dir);
    let def_skin = s_dir.join("default.png");
    if !def_skin.exists() {
        let _ = fs::write(&def_skin, DEFAULT_SKIN_BYTES);
    }
}

fn resources_dir(app: &AppHandle) -> PathBuf {
    if let Ok(exe) = std::env::current_exe() {
        if let Some(p) = exe.parent() {
            let candidate1 = p.join("resources");
            if candidate1.exists() {
                return candidate1;
            }
            if let Some(up) = p.parent().and_then(|p| p.parent()).and_then(|p| p.parent()) {
                let candidate2 = up.join("resources");
                if candidate2.exists() {
                    return candidate2;
                }
            }
        }
    }
    let direct = PathBuf::from("D:\\OpenCode\\launcher\\resources");
    if direct.exists() {
        return direct;
    }
    app.path().app_data_dir().unwrap_or_else(|_| PathBuf::from(".")).join("resources")
}

fn user_bg_dir(app: &AppHandle) -> PathBuf {
    app.path().app_data_dir().expect("app dir").join("backgrounds")
}

fn skins_dir(app: &AppHandle) -> PathBuf {
    app.path().app_data_dir().expect("app dir").join("skins")
}

fn game_root(_app: &AppHandle) -> PathBuf {
    let preferred = PathBuf::from("D:\\MineDash\\game");
    if preferred.parent().map(|p| p.exists()).unwrap_or(false) {
        preferred
    } else {
        dirs::data_dir()
            .expect("data dir")
            .join("MineDash Launcher")
            .join("game")
    }
}

fn load_store_from(path: &Path) -> StoreShape {
    let mut store: StoreShape = match fs::read_to_string(path) {
        Ok(raw) => serde_json::from_str(&raw).unwrap_or_default(),
        Err(_) => StoreShape::default(),
    };
    if store.lastVersion.is_empty() {
        store.lastVersion = default_version();
    }
    sanitize_settings(&mut store.settings);
    store
}

fn save_store_to(path: &Path, store: &StoreShape) {
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let _ = fs::write(path, serde_json::to_string_pretty(store).unwrap());
}

fn with_store<T>(state: &State<AppState>, f: impl FnOnce(&StoreShape) -> T) -> T {
    let guard = state.store.lock().unwrap();
    f(&guard)
}

fn patch_store<R>(app: &AppHandle, state: &State<AppState>, f: impl FnOnce(&mut StoreShape) -> R) -> R {
    let mut guard = state.store.lock().unwrap();
    let r = f(&mut guard);
    save_store_to(&store_file(app), &guard);
    r
}

// ─────────────────────────────────────────────────────────── backgrounds

fn bg_category(base: &str) -> &'static str {
    match base {
        "space" | "aurora" | "storm" => "Космос",
        "desert" | "canyon" | "volcano" => "Пустоши",
        "city" | "ruins" => "Город",
        "autumn" | "forest" | "birch" | "meadow" | "mountains" | "lake" | "swamp" | "sunrise" | "winter" => "Природа",
        _ => "Свои",
    }
}

fn list_backgrounds(app: &AppHandle) -> Vec<BackgroundMeta> {
    extract_builtin_resources(app);
    let mut out = Vec::new();
    let mut seen = std::collections::HashSet::new();
    let dirs = [(resources_dir(app).join("backgrounds"), true), (user_bg_dir(app), false)];
    for (dir, builtin) in dirs {
        let entries = match fs::read_dir(&dir) {
            Ok(e) => e,
            Err(_) => continue,
        };
        let mut names: Vec<String> = entries
            .filter_map(|e| e.ok())
            .map(|e| e.file_name().to_string_lossy().to_string())
            .filter(|f| {
                let l = f.to_lowercase();
                l.ends_with(".png") || l.ends_with(".jpg") || l.ends_with(".jpeg")
                    || l.ends_with(".webp") || l.ends_with(".gif")
                    || l.ends_with(".mp4") || l.ends_with(".webm")
            })
            .collect();
        names.sort();
        for f in names {
            if seen.contains(&f) {
                continue;
            }
            seen.insert(f.clone());
            let base = f.trim_end_matches(|c: char| c != '.').trim_end_matches('.').to_string();
            out.push(BackgroundMeta {
                id: format!("{}{}", if builtin { "b:" } else { "u:" }, f),
                name: base.replace(['-', '_'], " "),
                file: dir.join(&f).to_string_lossy().to_string(),
                builtin,
                category: bg_category(&base).to_string(),
            });
        }
    }
    out
}

fn current_skin(state: &State<AppState>, app: &AppHandle) -> Option<SkinPayload> {
    extract_builtin_resources(app);
    let (model, file) = with_store(state, |s| {
        (s.skin.clone().map(|k| k.model).unwrap_or_else(|| "classic".into()), s.skin.clone().and_then(|k| k.file))
    });
    let bytes = if let Some(f) = file {
        let path = skins_dir(app).join(f);
        fs::read(&path).unwrap_or_else(|_| DEFAULT_SKIN_BYTES.to_vec())
    } else {
        let path = skins_dir(app).join("default.png");
        fs::read(&path).unwrap_or_else(|_| DEFAULT_SKIN_BYTES.to_vec())
    };
    Some(SkinPayload {
        pngBase64: base64::engine::general_purpose::STANDARD.encode(&bytes),
        model,
    })
}

// ─────────────────────────────────────────────────────────── commands

#[tauri::command]
fn win_minimize(window: tauri::Window) {
    let _ = window.minimize();
}

#[tauri::command]
fn win_maximize(window: tauri::Window) {
    if window.is_maximized().unwrap_or(false) {
        let _ = window.unmaximize();
    } else {
        let _ = window.maximize();
    }
}

#[tauri::command]
fn win_close(window: tauri::Window) {
    let _ = window.close();
}

#[tauri::command]
fn win_is_maximized(window: tauri::Window) -> bool {
    window.is_maximized().unwrap_or(false)
}

#[tauri::command]
fn store_get(state: State<AppState>) -> StoreShape {
    with_store(&state, |s| s.clone())
}

#[tauri::command]
fn store_set_settings(app: AppHandle, state: State<AppState>, patch: serde_json::Value) -> Settings {
    patch_store(&app, &state, |s| {
        if let Some(p) = patch.as_object() {
            let mut merged = serde_json::to_value(&s.settings).unwrap();
            if let (Some(m), Some(sm)) = (merged.as_object_mut(), Some(p)) {
                for (k, v) in sm {
                    m.insert(k.clone(), v.clone());
                }
            }
            if let Ok(new_settings) = serde_json::from_value::<Settings>(merged) {
                s.settings = new_settings;
            }
        }
        s.settings.clone()
    })
}

#[tauri::command]
fn skin_get(state: State<AppState>, app: AppHandle) -> Option<SkinPayload> {
    current_skin(&state, &app)
}

#[tauri::command]
fn skin_set(app: AppHandle, state: State<AppState>, payload: SkinPayloadIn) -> Option<SkinPayload> {
    let b64 = payload.dataUrl.split(',').nth(1)?.to_string();
    let bytes = base64::engine::general_purpose::STANDARD.decode(b64).ok()?;
    let _ = fs::create_dir_all(skins_dir(&app));
    let name = format!("skin-{}.png", now_ms());
    fs::write(skins_dir(&app).join(&name), bytes.clone()).ok()?;
    sync_skin_to_quickskin(&app, &bytes, &payload.model);
    patch_store(&app, &state, |s| {
        s.skin = Some(Skin { model: payload.model, file: Some(name) });
    });
    current_skin(&state, &app)
}

#[derive(Deserialize)]
struct SkinPayloadIn {
    dataUrl: String,
    model: String,
}

#[tauri::command]
fn skin_set_model(app: AppHandle, state: State<AppState>, model: String) -> Option<SkinPayload> {
    patch_store(&app, &state, |s| {
        let file = s.skin.as_ref().and_then(|k| k.file.clone());
        s.skin = Some(Skin { model, file });
    });
    current_skin(&state, &app)
}

#[tauri::command]
fn skin_reset(app: AppHandle, state: State<AppState>) -> Option<SkinPayload> {
    patch_store(&app, &state, |s| {
        s.skin = None;
    });
    clear_quickskin_active(&app);
    current_skin(&state, &app)
}

/// Копирует скин в папку Quick Skin (game/quickskin/skins) и отмечает его активным
/// в config/quickskin-client.json, чтобы мод применял его в игре автоматически.
fn sync_skin_to_quickskin(app: &AppHandle, png: &[u8], model: &str) {
    use sha1::{Digest, Sha1};
    let game = game_root(app);
    let skins = game.join("quickskin").join("skins");
    if fs::create_dir_all(&skins).is_err() {
        return;
    }
    let hash: String = Sha1::digest(png).iter().map(|b| format!("{:02x}", b)).collect();
    let file = skins.join("minedash-skin.png");
    let _ = fs::write(&file, png);
    let md_dir = game.join("mdskin-skins");
    let _ = fs::create_dir_all(&md_dir);
    let _ = fs::write(md_dir.join("minedash-skin.png"), png);
    // активный скин
    let cfg_path = game.join("config").join("quickskin-client.json");
    let mut cfg: serde_json::Value = fs::read_to_string(&cfg_path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_else(|| serde_json::json!({}));
    if let Some(obj) = cfg.as_object_mut() {
        obj.insert("activeSkinHash".into(), serde_json::json!(hash.clone()));
        obj.insert("activeModelType".into(), serde_json::json!(model));
    }
    let _ = fs::write(&cfg_path, serde_json::to_string_pretty(&cfg).unwrap_or_default());

    // per-skin модель (skin-preferences.json)
    let prefs_path = game.join("config").join("skin-preferences.json");
    let mut prefs: serde_json::Value = fs::read_to_string(&prefs_path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_else(|| serde_json::json!({"preferences": {}}));
    let mut changed = false;
    if let Some(p) = prefs
        .as_object_mut()
        .and_then(|o| o.get_mut("preferences"))
        .and_then(|v| v.as_object_mut())
    {
        p.insert(hash, serde_json::json!({ "modelType": model }));
        changed = true;
    }
    if changed {
        let _ = fs::write(&prefs_path, serde_json::to_string_pretty(&prefs).unwrap_or_default());
    }
}

/// Сбрасывает активный скин Quick Skin при сбросе скина в лаунчере.
fn clear_quickskin_active(app: &AppHandle) {
    let game = game_root(app);
    let cfg_path = game.join("config").join("quickskin-client.json");
    if let Ok(raw) = fs::read_to_string(&cfg_path) {
        if let Ok(mut cfg) = serde_json::from_str::<serde_json::Value>(&raw) {
            if let Some(obj) = cfg.as_object_mut() {
                obj.insert("activeSkinHash".into(), serde_json::json!(""));
            }
            let _ = fs::write(&cfg_path, serde_json::to_string_pretty(&cfg).unwrap_or_default());
        }
    }
}

#[tauri::command]
fn backgrounds_list(app: AppHandle) -> Vec<BackgroundMeta> {
    list_backgrounds(&app)
}

#[tauri::command]
fn background_get_data_url(path: String) -> Option<String> {
    let bytes = fs::read(&path).ok()?;
    let mime = if path.ends_with(".png") {
        "image/png"
    } else if path.ends_with(".jpg") || path.ends_with(".jpeg") {
        "image/jpeg"
    } else if path.ends_with(".webp") {
        "image/webp"
    } else if path.ends_with(".gif") {
        "image/gif"
    } else {
        "image/png"
    };
    let b64 = base64::engine::general_purpose::STANDARD.encode(&bytes);
    Some(format!("data:{};base64,{}", mime, b64))
}

#[tauri::command]
fn backgrounds_add(app: AppHandle) -> Option<BackgroundMeta> {
    let picked = app
        .dialog()
        .file()
        .add_filter("Изображения и видео", &["png", "jpg", "jpeg", "webp", "gif", "mp4", "webm"])
        .blocking_pick_file()?;
    let src = picked.as_path()?.to_path_buf();
    let _ = fs::create_dir_all(user_bg_dir(&app));
    let base = src.file_name()?.to_string_lossy().to_string();
    let name = format!("{}-{}", now_ms(), base)
        .chars()
        .map(|c| if c.is_alphanumeric() || c == '.' || c == '-' || c == '_' { c } else { '_' })
        .collect::<String>();
    fs::copy(src, user_bg_dir(&app).join(&name)).ok()?;
    list_backgrounds(&app).into_iter().find(|b| b.file.ends_with(&name))
}

#[tauri::command]
fn backgrounds_remove(app: AppHandle, id: String) -> Vec<BackgroundMeta> {
    if let Some(meta) = list_backgrounds(&app).into_iter().find(|b| b.id == id) {
        if let Ok(canonical) = fs::canonicalize(&meta.file) {
            if let Ok(bg_root) = fs::canonicalize(user_bg_dir(&app)) {
                if canonical.starts_with(&bg_root) {
                    let _ = fs::remove_file(&meta.file);
                }
            }
        }
    }
    list_backgrounds(&app)
}

#[tauri::command]
fn app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

// ─────────────────────────────────────────────────────────── self-update

/// URL манифеста обновлений лаунчера (раздаётся nginx на VDS).
/// Переопределяется переменной окружения MINEDASH_UPDATE_URL (для тестов).
fn update_manifest_url() -> String {
    std::env::var("MINEDASH_UPDATE_URL")
        .unwrap_or_else(|_| "https://cdn.minedash.fun/launcher/version.json".into())
}

#[derive(Serialize, Deserialize, Clone)]
pub struct UpdateInfo {
    pub version: String,
    pub url: String,
    #[serde(default)]
    pub notes: String,
    #[serde(default)]
    pub sha256: String,
}

#[derive(Serialize)]
pub struct UpdateCheck {
    pub available: bool,
    pub current: String,
    pub info: Option<UpdateInfo>,
}

/// Сравнение версий a > b (semver-подобное, числовые сегменты).
fn semver_gt(a: &str, b: &str) -> bool {
    let pa: Vec<u64> = a.split('.').filter_map(|x| x.parse().ok()).collect();
    let pb: Vec<u64> = b.split('.').filter_map(|x| x.parse().ok()).collect();
    for i in 0..pa.len().max(pb.len()) {
        let va = pa.get(i).copied().unwrap_or(0);
        let vb = pb.get(i).copied().unwrap_or(0);
        if va != vb {
            return va > vb;
        }
    }
    false
}

#[tauri::command]
fn update_check() -> Result<UpdateCheck, String> {
    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| e.to_string())?;
    let resp = client
        .get(update_manifest_url())
        .send()
        .map_err(|e| format!("не удалось проверить обновления: {}", e))?;
    if !resp.status().is_success() {
        return Err(format!("проверка обновлений: HTTP {}", resp.status()));
    }
    let info: UpdateInfo = resp.json().map_err(|e| e.to_string())?;
    let current = env!("CARGO_PKG_VERSION").to_string();
    Ok(UpdateCheck {
        available: semver_gt(&info.version, &current),
        current,
        info: Some(info),
    })
}

/// Скачивает новый exe, пишет скрипт замены и перезапускает лаунчер.
#[tauri::command]
fn update_install(app: AppHandle) -> Result<(), String> {
    let check = update_check()?;
    if !check.available {
        return Err("обновлений нет".into());
    }
    let info = check.info.unwrap();

    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(600))
        .build()
        .map_err(|e| e.to_string())?;
    let bytes = client
        .get(&info.url)
        .send()
        .map_err(|e| format!("загрузка обновления: {}", e))?
        .bytes()
        .map_err(|e| e.to_string())?;

    // проверка SHA-256 (защита от подмены бинарника)
    if !info.sha256.is_empty() {
        let digest = {
            use sha2::{Digest, Sha256};
            let mut h = Sha256::new();
            h.update(&bytes);
            format!("{:x}", h.finalize())
        };
        if !digest.eq_ignore_ascii_case(&info.sha256) {
            return Err("Целостность обновления нарушена (SHA-256 не совпал)".into());
        }
    }

    let exe = std::env::current_exe().map_err(|e| e.to_string())?;
    let tmp_dir = std::env::temp_dir().join("minedash-update");
    let _ = fs::create_dir_all(&tmp_dir);
    let tmp = tmp_dir.join("minedash-launcher.new");
    fs::write(&tmp, &bytes).map_err(|e| format!("запись обновления: {}", e))?;

    let is_windows = cfg!(target_os = "windows");

    if is_windows {
        let bat = tmp_dir.join("minedash-update.bat");
        let bat_content = format!(
            "@echo off\r\n:wait\r\nping 127.0.0.1 -n 2 > nul\r\ndel \"{exe}\" 2>nul\r\nif exist \"{exe}\" goto wait\r\nmove /y \"{tmp}\" \"{exe}\"\r\nstart \"\" \"{exe}\"\r\ndel /f /q \"%~f0\"\r\ndel /f /q \"{vbs}\"\r\nrmdir /q \"{dir}\"\r\n",
            exe = exe.display(),
            tmp = tmp.display(),
            dir = tmp_dir.display(),
            vbs = tmp_dir.join("minedash-update.vbs").display()
        );
        fs::write(&bat, bat_content).map_err(|e| e.to_string())?;
        // VBScript для полностью скрытого запуска (без мигания консоли)
        let vbs = tmp_dir.join("minedash-update.vbs");
        let vbs_content = format!(
            "CreateObject(\"Wscript.Shell\").Run \"\"\"{}\"\"\", 0, False\r\n",
            bat.display()
        );
        fs::write(&vbs, vbs_content).map_err(|e| e.to_string())?;
        std::process::Command::new("wscript")
            .arg(&vbs)
            .spawn()
            .map_err(|e| format!("запуск обновления: {}", e))?;
    } else {
        let sh = tmp_dir.join("minedash-update.sh");
        let sh_content = format!(
            "#!/bin/bash\nsleep 2\nmv -f \"{tmp}\" \"{exe}\"\nchmod +x \"{exe}\"\nnohup \"{exe}\" >/dev/null 2>&1 &\nrm -rf \"{dir}\"\n",
            exe = exe.display(),
            tmp = tmp.display(),
            dir = tmp_dir.display()
        );
        fs::write(&sh, sh_content).map_err(|e| e.to_string())?;
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let _ = fs::set_permissions(&sh, fs::Permissions::from_mode(0o755));
        }
        std::process::Command::new("bash")
            .arg(&sh)
            .spawn()
            .map_err(|e| format!("запуск обновления: {}", e))?;
    }

    app.exit(0);
    Ok(())
}

// ─────────────────────────────────────────────────────────── workshop

#[derive(Serialize)]
pub struct ImportResult {
    theme: UserTheme,
    backgroundId: Option<String>,
}

/// Одна работа Workshop: тема + метаданные + локальная статистика.
#[derive(Serialize, Deserialize, Clone)]
pub struct WorkshopItem {
    pub id: String,
    pub title: String,
    pub author: String,
    pub description: String,
    /// палитра
    pub theme: UserTheme,
    /// base64 PNG фона (может отсутствовать)
    pub preview: Option<String>,
    pub likes: u64,
    pub downloads: u64,
    /// время публикации (ms)
    pub created: u64,
    /// установлен ли локально
    pub installed: bool,
    /// лайкнул ли текущий игрок
    #[serde(default)]
    pub liked: bool,
}

fn workshop_file(app: &AppHandle) -> PathBuf {
    app.path().app_data_dir().expect("app dir").join("workshop.json")
}

fn workshop_dir(app: &AppHandle) -> PathBuf {
    app.path().app_data_dir().expect("app dir").join("workshop")
}

fn list_workshop(app: &AppHandle) -> Vec<WorkshopItem> {
    match fs::read_to_string(workshop_file(app)) {
        Ok(raw) => serde_json::from_str(&raw).unwrap_or_default(),
        Err(_) => seed_workshop(app),
    }
}

fn save_workshop(app: &AppHandle, items: &[WorkshopItem]) {
    let _ = fs::create_dir_all(workshop_dir(app));
    let _ = fs::write(workshop_file(app), serde_json::to_string_pretty(items).unwrap());
}

/// Стартовые работы «от команды» — чтобы каталог не был пустым.
fn seed_workshop(app: &AppHandle) -> Vec<WorkshopItem> {
    let mk = |id: &str, title: &str, author: &str, desc: &str, theme: UserTheme| WorkshopItem {
        id: id.into(),
        title: title.into(),
        author: author.into(),
        description: desc.into(),
        theme,
        preview: None,
        likes: 0,
        downloads: 0,
        created: now_ms(),
        installed: false,
        liked: false,
    };
    let items = vec![
        mk("w-team-amber", "Amber Create", "MineDash Team", "Латунь и тёплое железо — дух Create.",
            UserTheme { name: "Amber Create".into(), author: "MineDash Team".into(), bgId: None,
                bg: "#100d0a".into(), panel: "#16120d".into(), panel2: "#1b1611".into(),
                line: "#282017".into(), line2: "#33291d".into(), line3: "#403425".into(),
                chip: "#1a150f".into(), chipHover: "#241d14".into(),
                accent: "#c4963e".into(), accentHover: "#d6a54a".into(),
                accentSoft: "rgba(196,150,62,0.16)".into(), cyan: "#d8b464".into() }),
        mk("w-team-aurora", "Aurora Night", "MineDash Team", "Холодное сияние для ночного вайба.",
            UserTheme { name: "Aurora Night".into(), author: "MineDash Team".into(), bgId: None,
                bg: "#060a12".into(), panel: "#0a0e18".into(), panel2: "#0d1220".into(),
                line: "#161c2c".into(), line2: "#1d2537".into(), line3: "#273142".into(),
                chip: "#111726".into(), chipHover: "#18202f".into(),
                accent: "#3d6cf0".into(), accentHover: "#4d7cf8".into(),
                accentSoft: "rgba(61,108,240,0.16)".into(), cyan: "#4fc3e8".into() }),
        mk("w-team-neon", "Neon City", "MineDash Team", "Розовый неон ночного города.",
            UserTheme { name: "Neon City".into(), author: "MineDash Team".into(), bgId: None,
                bg: "#080b12".into(), panel: "#0b0f18".into(), panel2: "#0e131e".into(),
                line: "#171e2b".into(), line2: "#1f2836".into(), line3: "#2a3546".into(),
                chip: "#121824".into(), chipHover: "#1a2231".into(),
                accent: "#e0417f".into(), accentHover: "#ee4f8d".into(),
                accentSoft: "rgba(224,65,127,0.16)".into(), cyan: "#45c7f0".into() }),
    ];
    save_workshop(app, &items);
    items
}

#[tauri::command]
fn workshop_list(app: AppHandle) -> Vec<WorkshopItem> {
    let mut items = list_workshop(&app);
    // в данных может остаться несколько «установленных» — оставляем одну
    let mut seen = false;
    let mut fixed = false;
    for it in items.iter_mut() {
        if it.installed {
            if seen {
                it.installed = false;
                fixed = true;
            } else {
                seen = true;
            }
        }
    }
    if fixed {
        save_workshop(&app, &items);
    }
    items
}

/// Публикация своей работы в каталог (локальный «сервер» сообщества).
#[tauri::command]
fn workshop_publish(app: AppHandle, state: State<AppState>, item: WorkshopItem) -> WorkshopItem {
    let mut items = list_workshop(&app);
    let mut item = item;
    item.id = format!("w-{}", now_ms());
    item.author = with_store(&state, |s| s.settings.nickname.clone()).is_empty()
        .then(|| "Игрок".to_string()).unwrap_or_else(|| item.author.clone());
    item.created = now_ms();
    items.push(item.clone());
    save_workshop(&app, &items);
    item
}

/// Установка: применяет тему + фон (если есть) из работы.
#[tauri::command]
fn workshop_install(app: AppHandle, state: State<AppState>, id: String) -> Result<ImportResult, String> {
    let items = list_workshop(&app);
    let item = items.iter().find(|i| i.id == id).ok_or("Работа не найдена")?;
    let theme = item.theme.clone();

    // фон из preview — в user-фоны
    let mut bg_id: Option<String> = None;
    let theme_bg_id = theme.bgId.clone();
    if let Some(preview) = &item.preview {
        if let Some(b64) = preview.split(',').nth(1) {
            if let Ok(png) = base64::engine::general_purpose::STANDARD.decode(b64) {
                let _ = fs::create_dir_all(user_bg_dir(&app));
                let name = format!("workshop-{}.png", now_ms());
                let _ = fs::write(user_bg_dir(&app).join(&name), png);
                bg_id = Some(format!("u:{}", name));
            }
        }
    }

    // помечаем установленной + счётчик загрузок; с остальных снимаем флаг
    let mut items = items;
    for it in items.iter_mut() {
        if it.id == id {
            it.installed = true;
            it.downloads += 1;
        } else {
            it.installed = false;
        }
    }
    save_workshop(&app, &items);

    patch_store(&app, &state, |s| {
        s.settings.userTheme = Some(theme.clone());
        let final_bg = bg_id.clone().or(theme_bg_id.clone());
        if let Some(id2) = &final_bg {
            s.settings.backgroundId = id2.clone();
        }
    });
    Ok(ImportResult { theme, backgroundId: bg_id })
}

/// Удаление: сброс userTheme (не удаляет файлы).
#[tauri::command]
fn workshop_uninstall(app: AppHandle, state: State<AppState>, id: String) {
    let mut items = list_workshop(&app);
    for it in items.iter_mut() {
        if it.id == id {
            it.installed = false;
        }
    }
    save_workshop(&app, &items);
    let _ = patch_store(&app, &state, |s| {
        s.settings.userTheme = None;
    });
}

/// Лайк: тоггл — один лайк на игрока, повторный клик снимает.
#[tauri::command]
fn workshop_like(app: AppHandle, id: String) -> Vec<WorkshopItem> {
    let mut items = list_workshop(&app);
    for it in items.iter_mut() {
        if it.id == id {
            if it.liked {
                it.liked = false;
                it.likes = it.likes.saturating_sub(1);
            } else {
                it.liked = true;
                it.likes += 1;
            }
        }
    }
    save_workshop(&app, &items);
    items
}

#[tauri::command]
fn theme_get(state: State<AppState>) -> Option<UserTheme> {
    with_store(&state, |s| s.settings.userTheme.clone())
}

#[tauri::command]
fn theme_set(app: AppHandle, state: State<AppState>, theme: UserTheme) -> UserTheme {
    let bg_id = theme.bgId.clone();
    patch_store(&app, &state, |s| {
        s.settings.userTheme = Some(theme.clone());
        if let Some(id) = &bg_id {
            s.settings.backgroundId = id.clone();
        }
    });
    theme
}

#[tauri::command]
fn theme_reset(app: AppHandle, state: State<AppState>) {
    patch_store(&app, &state, |s| {
        s.settings.userTheme = None;
    });
}

/// Экспорт темы в .mdstyle. Фон берётся из текущего backgroundId.
#[tauri::command]
fn theme_export(app: AppHandle, state: State<AppState>) -> Result<String, String> {
    let theme = with_store(&state, |s| s.settings.userTheme.clone())
        .ok_or("Пользовательская тема не задана — создайте её в Workshop")?;
    let bg_id = with_store(&state, |s| s.settings.backgroundId.clone());
    let bg_png = list_backgrounds(&app)
        .into_iter()
        .find(|b| b.id == bg_id)
        .and_then(|b| fs::read(&b.file).ok());
    let raw = theme.to_mdstyle(bg_png);
    // диалог сохранения
    let file = app
        .dialog()
        .file()
        .add_filter("MineDash Style", &["mdstyle"])
        .set_file_name(format!("{}.mdstyle", theme.name.replace([' ', '/'], "_")))
        .blocking_save_file()
        .ok_or("Сохранение отменено")?;
    let path = file.as_path().ok_or("Некорректный путь")?.to_path_buf();
    fs::write(&path, raw).map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().to_string())
}

/// Импорт темы из .mdstyle: сохраняет тему и внедряет фон (если есть) в user-фоны.
#[tauri::command]
fn theme_import(app: AppHandle, state: State<AppState>) -> Result<ImportResult, String> {
    #[derive(Serialize)]
    struct ImportResultInner {
        theme: UserTheme,
        backgroundId: Option<String>,
    }
    let _ = std::mem::size_of::<ImportResultInner>();

    let file = app
        .dialog()
        .file()
        .add_filter("MineDash Style", &["mdstyle"])
        .blocking_pick_file()
        .ok_or("Импорт отменён")?;
    let path = file.as_path().ok_or("Некорректный путь")?.to_path_buf();
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let (mut theme, bg_png) = UserTheme::from_mdstyle(&raw)?;

    // фон из файла — в user-фоны
    let mut bg_id: Option<String> = None;
    if let Some(png) = bg_png {
        let _ = fs::create_dir_all(user_bg_dir(&app));
        let name = format!("theme-{}.png", now_ms());
        let dest = user_bg_dir(&app).join(&name);
        fs::write(&dest, png).map_err(|e| e.to_string())?;
        bg_id = Some(format!("u:{}", name));
    }

    patch_store(&app, &state, |s| {
        s.settings.userTheme = Some(theme.clone());
        if let Some(id) = &bg_id {
            s.settings.backgroundId = id.clone();
        }
    });
    Ok(ImportResult { theme, backgroundId: bg_id })
}


#[tauri::command]
fn app_pick_java(app: AppHandle) -> Option<String> {
    let path = app
        .dialog()
        .file()
        .add_filter("java.exe", &["exe"])
        .blocking_pick_file()?;
    let p = path.as_path()?.to_path_buf();
    p.to_str().map(|s| s.to_string())
}

#[tauri::command]
fn app_open_external(app: AppHandle, url: String) {
    if url.starts_with("https://") {
        let _ = app.shell().open(url, None);
    }
}

#[tauri::command]
fn app_open_game_dir(app: AppHandle) {
    let _ = app.shell().open(game_root(&app).to_string_lossy().to_string(), None);
}

#[tauri::command]
fn app_set_last_server(app: AppHandle, state: State<AppState>, id: String) {
    patch_store(&app, &state, |s| {
        s.lastServer = id;
    });
}

// ─────────────────────────────────────────────────────────── auth

fn http_json(server_url: &str, api_path: &str, body: &str) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/{}", server_url.trim_end_matches('/'), api_path);
    dbg_log(&format!("http_json -> {}", url));
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(12))
        .connect_timeout(Duration::from_secs(8))
        .no_proxy()
        .build()
        .map_err(|e| e.to_string())?;
    let res = client
        .post(&url)
        .header("Content-Type", "application/json")
        .body(body.to_string())
        .send()
        .map_err(|e| { dbg_log(&format!("http_json error: {}", e)); "Сервер авторизации недоступен.".to_string() })?;
    dbg_log(&format!("http_json response: {}", res.status()));
    res.json().map_err(|_| "Некорректный ответ сервера.".to_string())
}

#[derive(Serialize)]
struct LoginResult {
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    auth: Option<AuthState>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[tauri::command]
fn auth_login(app: AppHandle, state: State<AppState>, nick: String, password: String) -> LoginResult {
    let url = with_store(&state, |s| s.settings.authUrl.clone());
    let body = serde_json::json!({ "nick": nick.trim(), "password": password }).to_string();
    match http_json(&url, "auth/login", &body) {
        Ok(v) if v.get("ok").and_then(|o| o.as_bool()).unwrap_or(false) => {
            let auth = AuthState {
                token: v.get("token").and_then(|t| t.as_str()).unwrap_or("").into(),
                nick: v.get("nick").and_then(|t| t.as_str()).unwrap_or("").into(),
                uuid: v.get("uuid").and_then(|t| t.as_str()).unwrap_or("").into(),
            };
            patch_store(&app, &state, |s| {
                s.auth = Some(auth.clone());
                s.settings.nickname = auth.nick.clone();
            });
            LoginResult { ok: true, auth: Some(auth), error: None }
        }
        Ok(v) => LoginResult {
            ok: false,
            auth: None,
            error: Some(v.get("error").and_then(|e| e.as_str()).unwrap_or("Неверный ник или пароль.").into()),
        },
        Err(e) => LoginResult { ok: false, auth: None, error: Some(e) },
    }
}

#[tauri::command]
fn auth_restore(app: AppHandle, state: State<AppState>) -> Option<AuthState> {
    let no_auth = std::env::var("MINEDASH_NO_AUTH").is_ok();
    if no_auth {
        #[cfg(not(debug_assertions))]
        {
            // в release — игнорируем, авторизация обязательна
        }
        #[cfg(debug_assertions)]
        let demo = AuthState {
            token: "demo".into(),
            nick: "L1keRR".into(),
            uuid: "00000000-0000-0000-0000-000000000000".into(),
        };
        #[cfg(debug_assertions)]
        patch_store(&app, &state, |s| {
            s.auth = Some(demo.clone());
            s.settings.nickname = demo.nick.clone();
        });
        #[cfg(debug_assertions)]
        return Some(demo);
    }
    let (url, cur) = with_store(&state, |s| (s.settings.authUrl.clone(), s.auth.clone()));
    let cur = cur?;
    let body = serde_json::json!({ "token": cur.token }).to_string();
    match http_json(&url, "auth/validate", &body) {
        Ok(v) if v.get("ok").and_then(|o| o.as_bool()).unwrap_or(false) => {
            let next = AuthState {
                token: cur.token,
                nick: v.get("nick").and_then(|t| t.as_str()).unwrap_or("").into(),
                uuid: v.get("uuid").and_then(|t| t.as_str()).unwrap_or("").into(),
            };
            patch_store(&app, &state, |s| {
                s.auth = Some(next.clone());
                s.settings.nickname = next.nick.clone();
            });
            Some(next)
        }
        _ => {
            patch_store(&app, &state, |s| {
                s.auth = None;
            });
            None
        }
    }
}

#[tauri::command]
fn auth_logout(app: AppHandle, state: State<AppState>) {
    let (url, cur) = with_store(&state, |s| (s.settings.authUrl.clone(), s.auth.clone()));
    if let Some(cur) = cur {
        let body = serde_json::json!({ "token": cur.token }).to_string();
        let _ = http_json(&url, "auth/logout", &body);
    }
    patch_store(&app, &state, |s| {
        s.auth = None;
    });
}

// ─────────────────────────────────────────────────────────── download & launch

#[allow(dead_code)]
fn sha1_of_file(path: &Path) -> Option<String> {
    use std::io::Read;
    let mut file = fs::File::open(path).ok()?;
    let mut h = Sha1::new();
    let mut buf = [0u8; 65536];
    loop {
        let n = file.read(&mut buf).ok()?;
        if n == 0 { break; }
        h.update(&buf[..n]);
    }
    Some(format!("{:x}", h.finalize()))
}

#[allow(dead_code)]
fn sha256_of_file(path: &Path) -> Option<String> {
    use std::io::Read;
    let mut file = fs::File::open(path).ok()?;
    let mut h = Sha256::new();
    let mut buf = [0u8; 65536];
    loop {
        let n = file.read(&mut buf).ok()?;
        if n == 0 { break; }
        h.update(&buf[..n]);
    }
    Some(format!("{:x}", h.finalize()))
}

fn is_safe_jar_name(name: &str) -> bool {
    let lower = name.to_lowercase();
    lower.ends_with(".jar")
        && !name.contains("..")
        && !name.contains('/')
        && !name.contains('\\')
        && !name.contains(':')
        && name.len() < 256
}

/// Удаляет инъекции аргументов JVM: -javaagent, -agentlib, -Xbootclasspath, отладчики и пр.
fn sanitize_jvm_args(user_args: &str) -> Vec<String> {
    let mut safe_args = Vec::new();
    let dangerous_prefixes = [
        "-javaagent",
        "-agentlib",
        "-agentpath",
        "-xbootclasspath",
        "-xrun",
        "-xdebug",
        "-xnoagent",
        "-djava.library.path",
        "-dorg.lwjgl",
        "-dminedash.",
        "-dfile.encoding",
        "-dstdout.encoding",
        "-dstderr.encoding",
        "--patch-module",
        "--module-path",
        "--add-opens",
        "--add-exports",
        "--add-reads",
        "--add-modules",
        "-cp",
        "-classpath",
        "--class-path",
        "-p",
    ];

    for arg in user_args.split_whitespace() {
        let trimmed = arg.trim();
        if trimmed.is_empty() || trimmed.len() > 256 {
            continue;
        }
        if trimmed.contains('\0') || trimmed.contains('\n') || trimmed.contains('\r') || trimmed.contains('"') {
            dbg_log(&format!("Anti-cheat: dropped malicious JVM arg: {}", trimmed));
            continue;
        }
        let lower = trimmed.to_lowercase();
        let is_dangerous = dangerous_prefixes.iter().any(|prefix| lower.starts_with(prefix));
        if is_dangerous {
            dbg_log(&format!("Anti-cheat: blocked dangerous JVM argument: {}", trimmed));
            continue;
        }

        // Разрешаем безопасные флаги оптимизации JVM
        if lower.starts_with("-xmx") || lower.starts_with("-xms") || lower.starts_with("-xss") || lower.starts_with("-xmn")
            || lower.starts_with("-xx:") || lower.starts_with("-d") {
            safe_args.push(trimmed.to_string());
        } else {
            dbg_log(&format!("Anti-cheat: filtered unrecognized JVM argument: {}", trimmed));
        }
    }

    safe_args
}

/// Проверяет наличие запущенных отладчиков и инжекторов памяти на Windows
#[cfg(target_os = "windows")]
fn check_blacklisted_processes() -> Result<(), String> {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x08000000;

    let output = match std::process::Command::new("tasklist")
        .args(["/FO", "CSV", "/NH"])
        .creation_flags(CREATE_NO_WINDOW)
        .output()
    {
        Ok(out) => out,
        Err(_) => return Ok(()),
    };

    let text = String::from_utf8_lossy(&output.stdout).to_lowercase();
    let blacklisted = [
        ("cheatengine", "Cheat Engine"),
        ("processhacker", "Process Hacker"),
        ("systeminformer", "System Informer"),
        ("x64dbg", "x64dbg"),
        ("x32dbg", "x32dbg"),
        ("ida64", "IDA Pro"),
        ("idag64", "IDA Pro"),
        ("ida.exe", "IDA Pro"),
        ("ollydbg", "OllyDbg"),
        ("dnspy", "dnSpy"),
        ("extremeinjector", "Extreme Injector"),
        ("artmoney", "ArtMoney"),
    ];

    for (needle, display_name) in blacklisted {
        if text.contains(needle) {
            dbg_log(&format!("Anti-cheat: detected blacklisted process: {}", display_name));
            return Err(format!(
                "Обнаружена активная программа отладки или изменения памяти ({})!\nЗакройте её перед запуском MineDash.",
                display_name
            ));
        }
    }

    Ok(())
}

#[cfg(not(target_os = "windows"))]
fn check_blacklisted_processes() -> Result<(), String> {
    Ok(())
}

const INTEGRITY_KEY: &[u8] = b"MineDash_AntiCheat_Guard_Secure_Key_2026_#91x";

fn compute_hmac_sha256(key: &[u8], data: &[u8]) -> String {
    let mut k = [0u8; 64];
    if key.len() > 64 {
        let mut hasher = Sha256::new();
        hasher.update(key);
        let res = hasher.finalize();
        k[..32].copy_from_slice(&res);
    } else {
        k[..key.len()].copy_from_slice(key);
    }

    let mut ipad = [0x36u8; 64];
    let mut opad = [0x5cu8; 64];
    for i in 0..64 {
        ipad[i] ^= k[i];
        opad[i] ^= k[i];
    }

    let mut inner = Sha256::new();
    inner.update(&ipad);
    inner.update(data);
    let inner_hash = inner.finalize();

    let mut outer = Sha256::new();
    outer.update(&opad);
    outer.update(&inner_hash);
    format!("{:x}", outer.finalize())
}

#[derive(Serialize, Deserialize, Default)]
struct IntegrityDb {
    hashes: std::collections::HashMap<String, String>,
    signature: String,
}

impl IntegrityDb {
    fn load(path: &Path) -> Option<std::collections::HashMap<String, String>> {
        let raw = fs::read_to_string(path).ok()?;
        let db: IntegrityDb = serde_json::from_str(&raw).ok()?;
        let canonical_str = serde_json::to_string(&db.hashes).ok()?;
        let expected_sig = compute_hmac_sha256(INTEGRITY_KEY, canonical_str.as_bytes());
        if db.signature == expected_sig {
            Some(db.hashes)
        } else {
            dbg_log("Anti-cheat: integrity database signature invalid! Tampering detected.");
            None
        }
    }

    fn save(path: &Path, hashes: &std::collections::HashMap<String, String>) {
        if let Ok(canonical_str) = serde_json::to_string(hashes) {
            let sig = compute_hmac_sha256(INTEGRITY_KEY, canonical_str.as_bytes());
            let db = IntegrityDb {
                hashes: hashes.clone(),
                signature: sig,
            };
            if let Ok(out) = serde_json::to_string_pretty(&db) {
                let _ = fs::write(path, out);
            }
        }
    }
}

/// Принудительно завершает процесс и все его дочерние процессы (дерево)
fn kill_process_tree(pid: u32) {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        let mut cmd = std::process::Command::new("taskkill");
        cmd.args(["/F", "/T", "/PID", &pid.to_string()]);
        cmd.creation_flags(0x08000000);
        let _ = cmd.output();
    }
    #[cfg(not(target_os = "windows"))]
    {
        let _ = pid;
    }
}

/// Блокирует файлы от записи, удаления и переименования на уровне ядра Windows NTFS
/// (share_mode = 1 / FILE_SHARE_READ: разрешает чтение, но полностью запрещает запись и удаление)
#[cfg(target_os = "windows")]
fn lock_directory_files(dir: &Path) -> Vec<fs::File> {
    use std::os::windows::fs::OpenOptionsExt;
    let mut handles = Vec::new();
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() {
                if let Ok(file) = fs::OpenOptions::new()
                    .read(true)
                    .share_mode(1)
                    .open(&path)
                {
                    handles.push(file);
                }
            }
        }
    }
    handles
}

#[cfg(not(target_os = "windows"))]
fn lock_directory_files(_dir: &Path) -> Vec<fs::File> {
    Vec::new()
}

/// Строгая синхронизация папки модов инстанса:
/// 1. Удаляет symlink / junction обходы
/// 2. Удаляет любые посторонние моды, скрипты, инжекторы и папки
/// 3. Сверяет точные размеры и SHA-256 хеши каждого мода с проверенным эталоном
/// 4. Перезаписывает любые повреждённые или подмененные файлы чистыми копиями
fn sync_instance_mods(root_mods: &Path, game_mods: &Path) -> Result<(), String> {
    if let Ok(meta) = fs::symlink_metadata(game_mods) {
        if meta.file_type().is_symlink() {
            dbg_log("Anti-cheat: game mods directory is a symlink! Removing junction.");
            let _ = fs::remove_file(game_mods);
        }
    }
    fs::create_dir_all(game_mods).map_err(|e| e.to_string())?;

    // 1. Собираем проверенные моды из root/mods с их размерами и SHA-256
    let mut clean_mods: std::collections::HashMap<String, (u64, Option<String>)> = std::collections::HashMap::new();
    if let Ok(entries) = fs::read_dir(root_mods) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() {
                let name = entry.file_name().to_string_lossy().to_string();
                if is_safe_jar_name(&name) {
                    if let Ok(meta) = fs::metadata(&path) {
                        let hash = sha256_of_file(&path);
                        clean_mods.insert(name, (meta.len(), hash));
                    }
                }
            }
        }
    }

    // 2. Очищаем game_mods от любых посторонних файлов и папок
    if let Ok(entries) = fs::read_dir(game_mods) {
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            if path.is_dir() {
                dbg_log(&format!("Anti-cheat: removing rogue directory from instance mods: {:?}", path));
                let _ = fs::remove_dir_all(&path);
                continue;
            }

            match clean_mods.get(&name) {
                None => {
                    // Чит-мод или посторонний файл
                    dbg_log(&format!("Anti-cheat: removing rogue/unauthorized file from instance mods: {}", name));
                    let _ = fs::remove_file(&path);
                }
                Some((expected_size, expected_hash)) => {
                    let mut is_valid = false;
                    if let Ok(meta) = fs::metadata(&path) {
                        if meta.len() == *expected_size {
                            if let Some(eh) = expected_hash {
                                if let Some(current_h) = sha256_of_file(&path) {
                                    if &current_h == eh {
                                        is_valid = true;
                                    }
                                }
                            } else {
                                is_valid = true;
                            }
                        }
                    }
                    if !is_valid {
                        dbg_log(&format!("Anti-cheat: instance mod {} SHA-256 or size mismatch! Overwriting with clean copy.", name));
                        let _ = fs::copy(root_mods.join(&name), &path);
                    }
                }
            }
        }
    }

    // 3. Копируем недостающие моды из root_mods в game_mods
    for (name, _) in &clean_mods {
        let dst = game_mods.join(name);
        if !dst.exists() {
            let src = root_mods.join(name);
            let _ = fs::copy(&src, &dst);
        }
    }

    Ok(())
}

fn file_ok(path: &Path, _sha1: Option<&str>, size: Option<u64>) -> bool {
    let st = match fs::metadata(path) {
        Ok(s) => s,
        Err(_) => return false,
    };
    if let Some(sz) = size {
        if st.len() != sz {
            return false;
        }
    }
    // SHA1 пропускаем — только размер (ускорение в ~50x)
    true
}

fn now_ms() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis() as u64
}

struct GameLayout {
    root: PathBuf,
    version_id: String,
    client_jar: PathBuf,
    assets_dir: PathBuf,
    natives_dir: PathBuf,
    libraries_dir: PathBuf,
    version_json: PathBuf,
}

fn game_layout(root: &Path, version_id: &str) -> GameLayout {
    let ver = root.join("versions").join(version_id);
    GameLayout {
        root: root.to_path_buf(),
        version_id: version_id.to_string(),
        client_jar: ver.join(format!("{}.jar", version_id)),
        assets_dir: root.join("assets").join("virtual").join("legacy"),
        natives_dir: ver.join("natives"),
        libraries_dir: root.join("libraries"),
        version_json: ver.join(format!("{}.json", version_id)),
    }
}

#[derive(Deserialize, Default)]
struct LibArtifact {
    path: Option<String>,
    url: Option<String>,
    sha1: Option<String>,
    size: Option<u64>,
}

#[derive(Deserialize)]
struct Rule {
    action: String,
    os: Option<OsRule>,
}

#[derive(Deserialize)]
struct OsRule {
    name: Option<String>,
}

#[derive(Deserialize)]
struct LibEntry {
    rules: Option<Vec<Rule>>,
    downloads: Option<Downloads>,
}

#[derive(Deserialize)]
struct Downloads {
    artifact: Option<LibArtifact>,
    classifiers: Option<std::collections::HashMap<String, LibArtifact>>,
}

#[derive(Deserialize)]
struct VersionJson {
    #[serde(default)]
    id: String,
    #[serde(default)]
    #[serde(rename = "type")]
    type_: String,
    #[serde(default)]
    assets: Option<String>,
    mainClass: String,
    #[serde(default)]
    downloads: Option<ClientDownloads>,
    #[serde(default)]
    assetIndex: Option<AssetIndex>,
    libraries: Vec<LibEntry>,
    arguments: Option<Args>,
    #[serde(default)]
    inheritsFrom: Option<String>,
}

#[derive(Deserialize)]
struct ClientDownloads {
    client: LibArtifact,
}

#[derive(Deserialize)]
struct AssetIndex {
    url: String,
}

#[derive(Deserialize)]
struct Args {
    #[serde(default)]
    jvm: Option<Vec<serde_json::Value>>,
    #[serde(default)]
    game: Option<Vec<serde_json::Value>>,
}

fn rules_allow(rules: &Option<Vec<Rule>>) -> bool {
    let rules = match rules {
        Some(r) if !r.is_empty() => r,
        _ => return true,
    };
    let mut allowed = false;
    for r in rules {
        if let Some(os) = &r.os {
            if let Some(name) = &os.name {
                if name != "windows" {
                    continue;
                }
            }
        }
        allowed = r.action == "allow";
    }
    allowed
}

fn emit_progress(app: &AppHandle, stage: &str, done: u64, total: u64, speed: u64) {
    dbg_log(&format!("emit_progress: {} {}/{}", stage, done, total));
    let _ = app.emit(
        "game:progress",
        ProgressState { stage: stage.into(), file: None, done, total, speed },
    );
}

fn fetch_json(url: &str) -> Result<serde_json::Value, String> {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(30))
        .connect_timeout(Duration::from_secs(15))
        .build()
        .map_err(|e| e.to_string())?;
    let res = client
        .get(url)
        .header("User-Agent", "MineDashLauncher/1.0")
        .send()
        .map_err(|e| format!("HTTP error: {}", e))?;
    res.json().map_err(|e| format!("JSON error: {}", e))
}

fn download_pool(
    app: AppHandle,
    stage: String,
    tasks: Vec<(String, PathBuf, Option<String>, Option<u64>)>,
    concurrency: usize,
) -> Result<(), String> {
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::sync::Arc;

    let total: u64 = tasks.iter().map(|t| t.3.unwrap_or(0)).sum();
    let queue: Vec<_> = tasks
        .into_iter()
        .filter(|t| !file_ok(&t.1, t.2.as_deref(), t.3))
        .collect();
    if queue.is_empty() {
        emit_progress(&app, &stage, total, total, 0);
        return Ok(());
    }
    let done = Arc::new(AtomicU64::new(0));
    let started = std::time::Instant::now();

    let idx = Arc::new(AtomicU64::new(0));
    let q = Arc::new(queue);

    let app_t = app.clone();
    let stage_t = stage.clone();
    let done_t = done.clone();
    let started_t = started;
    std::thread::spawn(move || {
        // progress ticker
        let app = app_t;
        let stage = stage_t;
        let done = done_t;
        let started = started_t;
        loop {
            let d = done.load(Ordering::SeqCst);
            let secs = started.elapsed().as_secs_f64();
            let speed = if secs > 0.0 { (d as f64 / secs) as u64 } else { 0 };
            emit_progress(&app, &stage, d, total, speed);
            if d >= total { break; }
            std::thread::sleep(Duration::from_millis(250));
        }
    });

    let (tx_done, rx_done) = std::sync::mpsc::channel::<Result<(), String>>();
    std::thread::spawn(move || {
        let mut handles = Vec::new();
        for _ in 0..concurrency {
            let idx = idx.clone();
            let q = q.clone();
            let done = done.clone();
            let tx = tx_done.clone();
            handles.push(std::thread::spawn(move || {
                loop {
                    let i = idx.fetch_add(1, Ordering::SeqCst) as usize;
                    if i >= q.len() {
                        break;
                    }
                    let (url, dest, sha, size) = &q[i];
                    let _ = size;
                    let mut retries = 3u32;
                    loop {
                        match download_one(url, dest, sha.as_deref()) {
                            Ok(n) => {
                                done.fetch_add(n, Ordering::SeqCst);
                                break;
                            }
                            Err(e) => {
                                retries -= 1;
                                if retries == 0 {
                                    let _ = tx.send(Err(e));
                                    return;
                                }
                                std::thread::sleep(Duration::from_millis(800));
                            }
                        }
                    }
                }
                let _ = tx.send(Ok(()));
            }));
        }
        for h in handles {
            let _ = h.join();
        }
    });

    for _ in 0..concurrency {
        if let Ok(Err(e)) = rx_done.recv() {
            return Err(e);
        }
    }
    emit_progress(&app, &stage, total, total, 0);
    Ok(())
}

fn download_one(url: &str, dest: &Path, sha1: Option<&str>) -> Result<u64, String> {
    if let Some(parent) = dest.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let tmp = dest.with_extension("part");
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(300))
        .connect_timeout(Duration::from_secs(15))
        .build()
        .map_err(|e| e.to_string())?;
    let mut res = client
        .get(url)
        .header("User-Agent", "MineDashLauncher/1.0")
        .send()
        .map_err(|e| format!("HTTP {}: {}", url, e))?;
    if !res.status().is_success() {
        return Err(format!("HTTP {} for {}", res.status(), url));
    }
    let mut buf: Vec<u8> = Vec::new();
    res.copy_to(&mut buf).map_err(|e| e.to_string())?;
    if let Some(hash) = sha1 {
        let mut h = Sha1::new();
        h.update(&buf);
        let actual = format!("{:x}", h.finalize());
        if actual != hash {
            return Err(format!("checksum mismatch: {}", url));
        }
    }
    fs::write(&tmp, &buf).map_err(|e| e.to_string())?;
    fs::rename(&tmp, dest).map_err(|e| e.to_string())?;
    Ok(buf.len() as u64)
}

fn ensure_java(app: &AppHandle, root: &Path) -> Result<PathBuf, String> {
    const ADOPTIUM: &str =
        "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse";
    let java_dir = root.join("runtime").join("jre21");
    let marker = java_dir.join("bin").join("java.exe");
    if marker.exists() {
        return Ok(marker);
    }
    emit_progress(app, "java", 0, 1, 0);
    fs::create_dir_all(&java_dir).map_err(|e| e.to_string())?;
    let zip = root.join("runtime").join("jre21.zip");
    download_pool(
        app.clone(),
        "java".into(),
        vec![(ADOPTIUM.into(), zip.clone(), None, None)],
        1,
    )?;
    emit_progress(app, "java", 1, 1, 0);
    let tmp = root.join("runtime").join("jre21-extract");
    unzip(&zip, &tmp)?;
    // в архиве один каталог верхнего уровня
    let inner = {
        let entries: Vec<_> = fs::read_dir(&tmp).map_err(|e| e.to_string())?
            .filter_map(|e| e.ok())
            .collect();
        if entries.len() == 1 && entries[0].path().is_dir() {
            entries[0].path()
        } else {
            tmp.clone()
        }
    };
    let _ = fs::remove_dir_all(&java_dir);
    fs::rename(&inner, &java_dir).map_err(|e| e.to_string())?;
    let _ = fs::remove_dir_all(&tmp);
    let _ = fs::remove_file(&zip);
    Ok(marker)
}

fn unzip(zip_path: &Path, dest: &Path) -> Result<(), String> {
    let file = fs::File::open(zip_path).map_err(|e| e.to_string())?;
    let mut archive = zip::ZipArchive::new(file).map_err(|e| e.to_string())?;
    fs::create_dir_all(dest).map_err(|e| e.to_string())?;
    for i in 0..archive.len() {
        let mut entry = archive.by_index(i).map_err(|e| e.to_string())?;
        if entry.is_dir() {
            continue;
        }
        // Zip Slip защита: только относительные пути без ..
        let name = entry.name().to_string();
        if name.contains("..") || name.starts_with('/') || name.starts_with('\\') || name.contains(':') {
            continue; // пропускаем опасные entry
        }
        let out_path = dest.join(&name);
        if let Some(parent) = out_path.parent() {
            fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        let mut out = fs::File::create(&out_path).map_err(|e| e.to_string())?;
        std::io::copy(&mut entry, &mut out).map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn ensure_game(
    app: &AppHandle,
    root: &Path,
    version_id: &str,
) -> Result<GameLayout, String> {
    const MANIFEST: &str = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json";
    let layout = game_layout(root, version_id);
    fs::create_dir_all(root.join("versions").join(version_id)).map_err(|e| e.to_string())?;

    emit_progress(app, "manifest", 0, 1, 0);
    let manifest = fetch_json(MANIFEST)?;
    let versions = manifest
        .get("versions")
        .and_then(|v| v.as_array())
        .ok_or("bad manifest")?;
    let entry = versions
        .iter()
        .find(|v| v.get("id").and_then(|i| i.as_str()) == Some(version_id))
        .ok_or(format!("версия {} не найдена в манифесте", version_id))?;
    let entry_url = entry
        .get("url")
        .and_then(|u| u.as_str())
        .ok_or("нет url версии")?
        .replace("piston-meta.mojang.com", "launchermeta.mojang.com");

    let vjson: VersionJson = if file_ok(&layout.version_json, None, None) {
        let raw = fs::read_to_string(&layout.version_json).map_err(|e| e.to_string())?;
        serde_json::from_str(&raw).map_err(|e| e.to_string())?
    } else {
        let client = reqwest::blocking::Client::new();
        let raw = client
            .get(&entry_url)
            .header("User-Agent", "MineDashLauncher/1.0")
            .send()
            .map_err(|e| e.to_string())?
            .text()
            .map_err(|e| e.to_string())?;
        fs::write(&layout.version_json, &raw).map_err(|e| e.to_string())?;
        serde_json::from_str(&raw).map_err(|e| e.to_string())?
    };

    // библиотеки + natives
    let mut tasks: Vec<(String, PathBuf, Option<String>, Option<u64>)> = Vec::new();
    let mut natives: Vec<(String, PathBuf, Option<String>, Option<u64>)> = Vec::new();
    for lib in &vjson.libraries {
        if !rules_allow(&lib.rules) {
            continue;
        }
        if let Some(art) = lib.downloads.as_ref().and_then(|d| d.artifact.as_ref()) {
            if let Some(url) = &art.url {
                tasks.push((
                    url.clone(),
                    layout.libraries_dir.join(art.path.as_deref().unwrap_or_default()),
                    art.sha1.clone(),
                    art.size,
                ));
            }
        }
        if let Some(cls) = lib
            .downloads
            .as_ref()
            .and_then(|d| d.classifiers.as_ref())
            .and_then(|c| c.get("natives-windows"))
        {
            if let Some(url) = &cls.url {
                let dest = layout.natives_dir.join(
                    Path::new(cls.path.as_deref().unwrap_or_default())
                        .file_name()
                        .unwrap_or_default(),
                );
                natives.push((url.clone(), dest.clone(), cls.sha1.clone(), cls.size));
                tasks.push((url.clone(), dest, cls.sha1.clone(), cls.size));
            }
        }
    }
    if let Some(dl) = &vjson.downloads {
        tasks.push((
            dl.client.url.clone().unwrap_or_default(),
            layout.client_jar.clone(),
            dl.client.sha1.clone(),
            dl.client.size,
        ));
    }

    let libs_total: u64 = tasks.iter().map(|t| t.3.unwrap_or(0)).sum();
    emit_progress(app, "libraries", 0, libs_total, 0);
    download_pool(app.clone(), "libraries".into(), tasks, 6)?;

    // распаковка natives
    for (url, dest, sha, _) in &natives {
        let _ = url;
        if !file_ok(dest, sha.as_deref(), None) {
            continue;
        }
        unzip(dest, &layout.natives_dir)?;
    }

    // ресурсы (пропускаем для NeoForge — наследуется от ванильной версии)
    if let Some(ai) = &vjson.assetIndex {
        emit_progress(app, "assets", 0, 1, 0);
        let index_url = ai.url
            .replace("piston-meta.mojang.com", "launchermeta.mojang.com");
        let index_dir = root.join("assets").join("indexes");
        fs::create_dir_all(&index_dir).map_err(|e| e.to_string())?;
        let asset_id = vjson.assets.clone().unwrap_or_else(|| "legacy".into());
        let index_file = index_dir.join(format!("{}.json", asset_id));
        let aindex: serde_json::Value = if index_file.exists() {
            let raw = fs::read_to_string(&index_file).map_err(|e| e.to_string())?;
            serde_json::from_str(&raw).map_err(|e| e.to_string())?
        } else {
            let v = fetch_json(&index_url)?;
            fs::write(&index_file, v.to_string()).map_err(|e| e.to_string())?;
            v
        };
        let objects = aindex
            .get("objects")
            .and_then(|o| o.as_object())
            .ok_or("bad asset index")?;
        let mut asset_tasks: Vec<(String, PathBuf, Option<String>, Option<u64>)> = Vec::new();
        let mut virtual_links: Vec<(String, String)> = Vec::new();
        for (name, obj) in objects {
            let hash = obj.get("hash").and_then(|h| h.as_str()).unwrap_or("");
            let size = obj.get("size").and_then(|s| s.as_u64());
            let prefix = &hash[..2.min(hash.len())];
            asset_tasks.push((
                format!("https://resources.download.minecraft.net/{}/{}", prefix, hash),
                root.join("assets").join("objects").join(prefix).join(hash),
                Some(hash.to_string()),
                size,
            ));
            virtual_links.push((name.clone(), hash.to_string()));
        }
        let assets_total: u64 = asset_tasks.iter().map(|t| t.3.unwrap_or(0)).sum();
        emit_progress(app, "assets", 0, assets_total, 0);
        download_pool(app.clone(), "assets".into(), asset_tasks, 8)?;

        // virtual legacy tree
        for (name, hash) in &virtual_links {
            let dest = layout.assets_dir.join(&name);
            let src = root.join("assets").join("objects").join(&hash[..2.min(hash.len())]).join(&hash);
            if let Some(parent) = dest.parent() {
                let _ = fs::create_dir_all(parent);
            }
            if fs::hard_link(&src, &dest).is_err() {
                let _ = fs::copy(&src, &dest);
            }
        }
    }
    Ok(layout)
}

/// Устанавливает NeoForge-клиент и моды. Возвращает version_id NeoForge.
fn ensure_neoforge(app: &AppHandle, root: &Path, java_exe: &Path, vanilla_version: &str) -> Result<String, String> {
    const NF_VERSION: &str = "21.1.251";
    const NF_MC: &str = "1.21.1";
    let nf_id = format!("neoforge-{}", NF_VERSION);
    let nf_dir = root.join("versions").join(&nf_id);
    let nf_json = nf_dir.join(format!("{}.json", nf_id));

    // уже установлен?
    if nf_json.exists() {
        // проверим моды
        ensure_mods(app, root)?;
        ensure_overrides(app, root)?;
        return Ok(nf_id);
    }

    emit_progress(app, "neoforge", 0, 1, 0);

    // NeoForge installer требует launcher_profiles.json
    let profiles = root.join("launcher_profiles.json");
    if !profiles.exists() {
        fs::write(&profiles, r#"{"profiles":{},"settings":{"version":3}}"#).map_err(|e| e.to_string())?;
    }

    // скачиваем installer
    let installer_url = format!(
        "https://maven.neoforged.net/releases/net/neoforged/neoforge/{}/neoforge-{}-installer.jar",
        NF_VERSION, NF_VERSION
    );
    let installer = root.join("neoforge-installer.jar");
    download_one(&installer_url, &installer, None)?;

    // запускаем installer
    emit_progress(app, "neoforge", 1, 2, 0);
    let mut nf_cmd = std::process::Command::new(java_exe);
    nf_cmd.args(["-Xmx2G", "-jar", &installer.to_string_lossy(), "--installClient", &root.to_string_lossy()]);
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        nf_cmd.creation_flags(0x08000000);
    }
    let output = nf_cmd.output().map_err(|e| format!("NeoForge installer: {}", e))?;

    let _ = fs::remove_file(&installer);

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        dbg_log(&format!("NeoForge installer failed. stdout: {} stderr: {}", &stdout[..stdout.len().min(500)], &stderr[..stderr.len().min(500)]));
        return Err(format!("NeoForge installer error: {}", &stderr[..stderr.len().min(200)]));
    }

    // NeoForge создаёт версию с именем вида "neoforge-21.1.251"
    // но может создать и другое имя — ищем
    let versions_dir = root.join("versions");
    let mut found = None;
    if let Ok(entries) = fs::read_dir(&versions_dir) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if name.contains("neoforge") || name.contains("forge") {
                let j = entry.path().join(format!("{}.json", name));
                if j.exists() {
                    found = Some(name);
                    break;
                }
            }
        }
    }

    let nf_id = found.ok_or("NeoForge не создал версию")?;

    // скачиваем дополнительные библиотеки NeoForge
    let nf_json = versions_dir.join(&nf_id).join(format!("{}.json", nf_id));
    let raw = fs::read_to_string(&nf_json).map_err(|e| e.to_string())?;
    let nf_vjson: VersionJson = serde_json::from_str(&raw).map_err(|e| e.to_string())?;

    let mut tasks: Vec<(String, PathBuf, Option<String>, Option<u64>)> = Vec::new();
    for lib in &nf_vjson.libraries {
        if !rules_allow(&lib.rules) {
            continue;
        }
        if let Some(art) = lib.downloads.as_ref().and_then(|d| d.artifact.as_ref()) {
            if let Some(url) = &art.url {
                let dest = root.join("libraries").join(art.path.as_deref().unwrap_or_default());
                if !file_ok(&dest, art.sha1.as_deref(), art.size) {
                    tasks.push((url.clone(), dest, art.sha1.clone(), art.size));
                }
            }
        }
    }
    if !tasks.is_empty() {
        let total: u64 = tasks.iter().map(|t| t.3.unwrap_or(0)).sum();
        emit_progress(app, "neoforge-libs", 0, total, 0);
        download_pool(app.clone(), "neoforge-libs".into(), tasks, 6)?;
    }

    emit_progress(app, "neoforge", 2, 2, 0);

    // моды
    ensure_mods(app, root)?;
    ensure_overrides(app, root)?;

    Ok(nf_id)
}

/// Скачивает моды с CDN в папку mods и синхронизирует с проверенным списком и криптографической HMAC-базой хешей.
fn ensure_mods(app: &AppHandle, root: &Path) -> Result<(), String> {
    let auth_url = with_store(&app.state::<AppState>(), |s| s.settings.authUrl.clone());
    let (cdn_mods, cdn_list) = if auth_url.contains("minedash.fun") {
        (
            "https://cdn.minedash.fun/modpack/mods".to_string(),
            "https://cdn.minedash.fun/modpack/mods.json".to_string(),
        )
    } else {
        let base = auth_url.trim_end_matches('/');
        (
            format!("{}/modpack/mods", base),
            format!("{}/modpack/mods.json", base),
        )
    };
    let mods_dir = root.join("mods");
    fs::create_dir_all(&mods_dir).map_err(|e| e.to_string())?;

    let integrity_file = root.join(".integrity.json");
    let mut saved_hashes = IntegrityDb::load(&integrity_file).unwrap_or_default();

    // получаем список модов с CDN (поддерживаем как массив, так и объект { "files": [...], "sizes": {...} })
    let mut approved: std::collections::HashMap<String, Option<u64>> = std::collections::HashMap::new();

    if let Ok(v) = fetch_json(&cdn_list) {
        if let Some(files) = v.get("files").and_then(|f| f.as_array()) {
            let sizes = v.get("sizes").and_then(|s| s.as_object());
            for f in files {
                if let Some(name) = f.as_str() {
                    if is_safe_jar_name(name) {
                        let sz = sizes.and_then(|m| m.get(name)).and_then(|val| val.as_u64());
                        approved.insert(name.to_string(), sz);
                    }
                }
            }
        } else if let Some(files) = v.as_array() {
            for f in files {
                if let Some(name) = f.as_str() {
                    if is_safe_jar_name(name) {
                        approved.insert(name.to_string(), None);
                    }
                }
            }
        }
    }

    // Добавляем встроенный мод авторизации minedashauth, если он есть в ресурсах или сборке
    let local_auth_mod = resources_dir(app).join("minedashauth-1.0.0.jar");
    let fallback_auth_mod = PathBuf::from("D:\\OpenCode\\launcher\\Mod\\build\\libs\\minedashauth-1.0.0.jar");
    let auth_mod_src = if local_auth_mod.exists() {
        Some(local_auth_mod)
    } else if fallback_auth_mod.exists() {
        Some(fallback_auth_mod)
    } else {
        None
    };

    if let Some(src) = &auth_mod_src {
        let dst = mods_dir.join("minedashauth-1.0.0.jar");
        let _ = fs::copy(src, &dst);
        let sz = fs::metadata(&dst).ok().map(|m| m.len());
        approved.insert("minedashauth-1.0.0.jar".to_string(), sz);
    }

    // Добавляем встроенный мод скинов mdskin
    let local_skin = resources_dir(app).join("mdskin-1.0.0.jar");
    let fallback_skin = PathBuf::from("D:\\OpenCode\\admin\\mdskin\\build\\libs\\mdskin-1.0.0.jar");
    let skin_src = if local_skin.exists() { Some(local_skin) } else if fallback_skin.exists() { Some(fallback_skin) } else { None };
    if let Some(src) = &skin_src {
        let dst = mods_dir.join("mdskin-1.0.0.jar");
        let _ = fs::copy(src, &dst);
        let sz = fs::metadata(&dst).ok().map(|m| m.len());
        approved.insert("mdskin-1.0.0.jar".to_string(), sz);
    } else if mods_dir.join("mdskin-1.0.0.jar").exists() {
        let sz = fs::metadata(mods_dir.join("mdskin-1.0.0.jar")).ok().map(|m| m.len());
        approved.insert("mdskin-1.0.0.jar".to_string(), sz);
    } else if mods_dir.join("minedashauth-1.0.0.jar").exists() {
        let sz = fs::metadata(mods_dir.join("minedashauth-1.0.0.jar")).ok().map(|m| m.len());
        approved.insert("minedashauth-1.0.0.jar".to_string(), sz);
    }

    if approved.is_empty() {
        dbg_log("ensure_mods: no approved mods list available (network offline or CDN empty)");
        return Ok(());
    }

    // синхронизация: удаляем локальные файлы, которых нет в списке разрешенных модов,
    // либо файлы с несовпадающим размером / подмененным SHA-256 хешем
    if let Ok(entries) = fs::read_dir(&mods_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            if path.is_dir() {
                dbg_log(&format!("Anti-cheat: removing directory from root mods: {:?}", path));
                let _ = fs::remove_dir_all(&path);
                continue;
            }
            if !approved.contains_key(&name) {
                dbg_log(&format!("Anti-cheat: removing unknown file from root mods: {}", name));
                let _ = fs::remove_file(&path);
                saved_hashes.remove(&name);
            } else {
                let mut valid = true;
                if let Some(Some(expected_size)) = approved.get(&name) {
                    if let Ok(meta) = fs::metadata(&path) {
                        if meta.len() != *expected_size {
                            dbg_log(&format!("Anti-cheat: mod {} size mismatch ({} vs {}). Re-downloading.", name, meta.len(), expected_size));
                            valid = false;
                        }
                    } else {
                        valid = false;
                    }
                }
                // Проверяем SHA-256 по сохраненной подписанной HMAC базе
                if valid {
                    if let Some(expected_hash) = saved_hashes.get(&name) {
                        if let Some(actual_hash) = sha256_of_file(&path) {
                            if &actual_hash != expected_hash {
                                dbg_log(&format!("Anti-cheat: mod {} SHA-256 hash mismatch! File was tampered with on disk.", name));
                                valid = false;
                            }
                        }
                    } else if let Some(actual_hash) = sha256_of_file(&path) {
                        // Первичная регистрация хеша проверенного файла
                        saved_hashes.insert(name.clone(), actual_hash);
                    }
                }
                if !valid {
                    let _ = fs::remove_file(&path);
                    saved_hashes.remove(&name);
                }
            }
        }
    }

    // скачиваем только те, которых нет локально
    let mut tasks: Vec<(String, PathBuf, Option<String>, Option<u64>)> = Vec::new();
    for (name, expected_size) in &approved {
        let dest = mods_dir.join(name);
        if !dest.exists() {
            let encoded: String = name.chars().map(|c| match c {
                ' ' => "%20".to_string(),
                '(' => "%28".to_string(),
                ')' => "%29".to_string(),
                '[' => "%5B".to_string(),
                ']' => "%5D".to_string(),
                _ => c.to_string(),
            }).collect();
            tasks.push((format!("{}/{}", cdn_mods, encoded), dest, None, *expected_size));
        }
    }

    if !tasks.is_empty() {
        let needs_head = tasks.iter().any(|t| t.3.is_none());
        let tasks: Vec<(String, PathBuf, Option<String>, Option<u64>)> = if needs_head {
            let client = reqwest::blocking::Client::builder()
                .timeout(Duration::from_secs(15))
                .build()
                .map_err(|e| e.to_string())?;
            tasks
                .into_iter()
                .map(|(url, dest, sha, size)| {
                    let s = size.or_else(|| {
                        client.head(&url).send().ok()
                            .and_then(|r| r.headers().get("content-length").and_then(|v| v.to_str().ok().and_then(|s| s.parse().ok())))
                    });
                    (url, dest, sha, s)
                })
                .collect()
        } else {
            tasks
        };

        let total: u64 = tasks.iter().map(|t| t.3.unwrap_or(0)).sum();
        emit_progress(app, "mods", 0, total, 0);
        download_pool(app.clone(), "mods".into(), tasks, 6)?;

        // Вычисляем и сохраняем SHA-256 хеши для скачанных модов
        for (name, _) in &approved {
            let dest = mods_dir.join(name);
            if dest.exists() && !saved_hashes.contains_key(name) {
                if let Some(hash) = sha256_of_file(&dest) {
                    saved_hashes.insert(name.clone(), hash);
                }
            }
        }
    }

    // Сохраняем криптографически подписанную базу целостности
    IntegrityDb::save(&integrity_file, &saved_hashes);

    Ok(())
}

/// Скачивает и синхронизирует архив конфигураций и KubeJS скриптов (overrides.zip) с CDN
fn ensure_overrides(app: &AppHandle, root: &Path) -> Result<(), String> {
    let auth_url = with_store(&app.state::<AppState>(), |s| s.settings.authUrl.clone());
    let (cdn_base, cdn_list) = if auth_url.contains("minedash.fun") {
        (
            "https://cdn.minedash.fun/modpack".to_string(),
            "https://cdn.minedash.fun/modpack/mods.json".to_string(),
        )
    } else {
        let base = auth_url.trim_end_matches('/');
        (
            format!("{}/modpack", base),
            format!("{}/modpack/mods.json", base),
        )
    };

    let manifest_val = match fetch_json(&cdn_list) {
        Ok(v) => v,
        Err(_) => return Ok(()),
    };

    let overrides_info = manifest_val.get("overrides");
    if overrides_info.is_none() || overrides_info.unwrap().is_null() {
        return Ok(());
    }
    let overrides_obj = overrides_info.unwrap();
    let expected_hash = match overrides_obj.get("hash").and_then(|h| h.as_str()) {
        Some(h) if !h.is_empty() => h.to_lowercase(),
        _ => return Ok(()),
    };

    let hash_file = root.join(".overrides_hash");
    let current_hash = fs::read_to_string(&hash_file).unwrap_or_default().trim().to_lowercase();

    if !current_hash.is_empty() && current_hash == expected_hash {
        // Конфиги и KubeJS актуальны
        return Ok(());
    }

    emit_progress(app, "Синхронизация конфигов и KubeJS", 0, 1, 0);

    let zip_filename = overrides_obj.get("file").and_then(|f| f.as_str()).unwrap_or("overrides.zip");
    let zip_url = format!("{}/{}", cdn_base, zip_filename);

    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| e.to_string())?;

    let res = client.get(&zip_url).send().map_err(|e| format!("Не удалось скачать конфиги: {}", e))?;
    if !res.status().is_success() {
        dbg_log(&format!("ensure_overrides: server returned status {}", res.status()));
        return Ok(());
    }

    let bytes = res.bytes().map_err(|e| e.to_string())?;

    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    let actual_hash = format!("{:x}", hasher.finalize()).to_lowercase();

    if actual_hash != expected_hash {
        dbg_log(&format!("Overrides SHA-256 mismatch: expected {}, got {}", expected_hash, actual_hash));
        return Ok(());
    }

    let tmp_zip = root.join("overrides_temp.zip");
    fs::write(&tmp_zip, &bytes).map_err(|e| e.to_string())?;

    // Распаковываем в root
    let _ = unzip(&tmp_zip, root);

    // Распаковываем также во все существующие инстансы
    let instances_dir = root.join("instances");
    if instances_dir.exists() {
        if let Ok(entries) = fs::read_dir(&instances_dir) {
            for entry in entries.flatten() {
                let p = entry.path();
                if p.is_dir() {
                    let _ = unzip(&tmp_zip, &p);
                }
            }
        }
    }

    let _ = fs::remove_file(&tmp_zip);
    let _ = fs::write(&hash_file, &expected_hash);

    dbg_log(&format!("Overrides (configs & kubejs) successfully synced. Hash: {}", expected_hash));
    Ok(())
}

/// Рекурсивное копирование/обновление файлов директории
fn sync_dir_recursive(src: &Path, dst: &Path) -> Result<(), String> {
    if !src.exists() {
        return Ok(());
    }
    fs::create_dir_all(dst).map_err(|e| e.to_string())?;
    if let Ok(entries) = fs::read_dir(src) {
        for entry in entries.flatten() {
            let p = entry.path();
            let name = entry.file_name();
            let target = dst.join(name);
            if p.is_dir() {
                sync_dir_recursive(&p, &target)?;
            } else if p.is_file() {
                let need_copy = if let (Ok(sm), Ok(tm)) = (fs::metadata(&p), fs::metadata(&target)) {
                    sm.len() != tm.len()
                } else {
                    true
                };
                if need_copy {
                    let _ = fs::copy(&p, &target);
                }
            }
        }
    }
    Ok(())
}

fn substitute(tpl: &str, vars: &std::collections::HashMap<String, String>) -> String {
    let mut out = tpl.to_string();
    for (k, v) in vars {
        out = out.replace(&format!("${{{}}}", k), v);
    }
    out
}

fn build_command(
    layout: &GameLayout,
    java_exe: &Path,
    settings: &Settings,
    auth: &AuthState,
) -> Result<(Vec<String>, PathBuf), String> {
    let raw = fs::read_to_string(&layout.version_json).map_err(|e| e.to_string())?;
    let vjson: VersionJson = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let root = &layout.root;
    let game_dir = root.join("instances").join(&layout.version_id);
    fs::create_dir_all(&game_dir).map_err(|e| e.to_string())?;

    // Синхронизация и защита модов в каталоге инстанса (NeoForge ищет их там)
    let src_mods = root.join("mods");
    if src_mods.exists() {
        let dst_mods = game_dir.join("mods");
        sync_instance_mods(&src_mods, &dst_mods)?;
    }

    // Синхронизация конфигов и KubeJS в инстанс игры
    let _ = sync_dir_recursive(&root.join("config"), &game_dir.join("config"));
    let _ = sync_dir_recursive(&root.join("kubejs"), &game_dir.join("kubejs"));
    let _ = sync_dir_recursive(&root.join("defaultconfigs"), &game_dir.join("defaultconfigs"));
    let _ = sync_dir_recursive(&root.join("quickskin"), &game_dir.join("quickskin"));
    let _ = sync_dir_recursive(&root.join("mdskin-skins"), &game_dir.join("mdskin-skins"));

    // для NeoForge: подтягиваем родительскую (ванильную) версию
    let parent_vjson: Option<VersionJson> = if let Some(parent_id) = &vjson.inheritsFrom {
        let parent_json = root.join("versions").join(parent_id).join(format!("{}.json", parent_id));
        if parent_json.exists() {
            let raw = fs::read_to_string(&parent_json).map_err(|e| e.to_string())?;
            serde_json::from_str(&raw).ok()
        } else {
            None
        }
    } else {
        None
    };

    let natives_tmp = std::env::temp_dir().join(format!("minedash-natives-{}", layout.version_id));
    if natives_tmp.exists() {
        let _ = fs::remove_dir_all(&natives_tmp);
    }
    fs::create_dir_all(&natives_tmp).map_err(|e| e.to_string())?;
    if layout.natives_dir.exists() {
        for entry in fs::read_dir(&layout.natives_dir).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.is_file() {
                let name = entry.file_name().to_string_lossy().to_string();
                let lower = name.to_lowercase();
                if lower.ends_with(".dll") {
                    let _ = fs::copy(&path, natives_tmp.join(&name));
                }
            }
        }
    }

    let asset_id = vjson.assets.clone()
        .or_else(|| parent_vjson.as_ref().and_then(|p| p.assets.clone()))
        .unwrap_or_else(|| "legacy".into());

    let mut vars: std::collections::HashMap<String, String> = std::collections::HashMap::new();
    vars.insert("natives_directory".into(), natives_tmp.to_string_lossy().to_string());
    vars.insert("library_directory".into(), layout.libraries_dir.to_string_lossy().to_string());
    vars.insert("classpath_separator".into(), ";".into());
    vars.insert("launcher_name".into(), "MineDashLauncher".into());
    vars.insert("launcher_version".into(), "1.0.0".into());
    vars.insert("version_name".into(), vjson.id.clone());
    vars.insert("game_directory".into(), game_dir.to_string_lossy().to_string());
    vars.insert("assets_root".into(), root.join("assets").to_string_lossy().to_string());
    vars.insert("game_assets".into(), layout.assets_dir.to_string_lossy().to_string());
    vars.insert("assets_index_name".into(), asset_id);
    vars.insert("user_properties".into(), "{}".into());
    vars.insert("version_type".into(), vjson.type_.clone().into());
    vars.insert("resolution_width".into(), settings.resolutionW.to_string());
    vars.insert("resolution_height".into(), settings.resolutionH.to_string());
    vars.insert("auth_player_name".into(), auth.nick.clone());
    vars.insert("auth_uuid".into(), auth.uuid.clone());
    vars.insert("auth_access_token".into(), "0".into());
    vars.insert("auth_session".into(), "token:0".into());
    vars.insert("user_type".into(), "legacy".into());
    vars.insert("clientid".into(), "".into());
    vars.insert("auth_xuid".into(), "".into());
    vars.insert("classpath".into(), "".into());
    vars.insert("quickPlayPath".into(), "".into());
    vars.insert("quickPlaySingleplayer".into(), "".into());
    vars.insert("quickPlayMultiplayer".into(), "".into());
    vars.insert("quickPlayRealms".into(), "".into());

    // classpath: сначала библиотеки родителя (ваниль), потом NeoForge, без дубликатов
    let mut cp: Vec<String> = Vec::new();
    let mut seen: std::collections::HashSet<String> = std::collections::HashSet::new();
    if let Some(parent) = &parent_vjson {
        for lib in &parent.libraries {
            if !rules_allow(&lib.rules) {
                continue;
            }
            if let Some(art) = lib.downloads.as_ref().and_then(|d| d.artifact.as_ref()) {
                if let Some(p) = &art.path {
                    let path = layout.libraries_dir.join(p).to_string_lossy().to_string();
                    if seen.insert(path.clone()) {
                        cp.push(path);
                    }
                }
            }
        }
    }
    for lib in &vjson.libraries {
        if !rules_allow(&lib.rules) {
            continue;
        }
        if let Some(art) = lib.downloads.as_ref().and_then(|d| d.artifact.as_ref()) {
            if let Some(p) = &art.path {
                let path = layout.libraries_dir.join(p).to_string_lossy().to_string();
                if seen.insert(path.clone()) {
                    cp.push(path);
                }
            }
        }
    }
    // client jar: для ванильной версии; NeoForge (BootstrapLauncher) сам добавляет клиент
    if vjson.inheritsFrom.is_none() {
        cp.push(layout.client_jar.to_string_lossy().to_string());
    }
    let classpath = cp.join(";");
    vars.insert("classpath".into(), classpath.clone());

    let mut args: Vec<String> = Vec::new();
    let is_neoforge = vjson.inheritsFrom.is_some();
    args.push(format!("-Xmx{}M", settings.memoryMb));
    args.push(format!("-Xms{}M", (settings.memoryMb / 4).max(512)));
    // JVM-оптимизации для Minecraft
    args.push("-XX:+UseG1GC".into());
    args.push("-XX:+ParallelRefProcEnabled".into());
    args.push("-XX:MaxGCPauseMillis=200".into());
    args.push("-XX:+DisableExplicitGC".into());
    args.push("-Dfile.encoding=UTF-8".into());
    args.push("-Dstdout.encoding=UTF-8".into());
    args.push("-Dstderr.encoding=UTF-8".into());
    args.push(format!("-Djava.library.path={}", natives_tmp.to_string_lossy()));
    args.push("-Dminecraft.launcher.brand=MineDashLauncher".into());
    args.push("-Dminecraft.launcher.version=1.0.0".into());
    // Anti-cheat: полное отключение JVM Attach API (блокировка инъекций Java-агентов)
    args.push("-XX:+DisableAttachMechanism".into());
    args.push("-Djdk.attach.allowAttachSelf=false".into());
    // ускоряем загрузку NeoForge: пропускаем проверки сертификатов
    if is_neoforge {
        args.push("-Dfml.ignoreInvalidMinecraftCertificates=true".into());
        args.push("-Dfml.ignorePatchDiscrepancies=true".into());
    }
    // отключаем EarlyDisplay NeoForge (зависает на некоторых системах)
    if is_neoforge {
        let fml_toml = game_dir.join("config").join("fml.toml");
        if let Some(parent) = fml_toml.parent() {
            let _ = fs::create_dir_all(parent);
        }
        // принудительно перезаписываем конфиг
        let content = fs::read_to_string(&fml_toml).unwrap_or_default();
        let content = content
            .replace("earlyWindowControl = true", "earlyWindowControl = false")
            .replace("earlyWindowProvider = \"fmlearlywindow\"", "earlyWindowProvider = \"off\"");
        let _ = fs::write(&fml_toml, content);
    }
    if !settings.jvmArgs.trim().is_empty() {
        let safe_user_args = sanitize_jvm_args(&settings.jvmArgs);
        for a in safe_user_args {
            args.push(a);
        }
    }

    // MineDash Auth mod integration & properties
    args.push(format!("-Dminedash.auth.token={}", auth.token));
    args.push(format!("-Dminedash.auth.nick={}", auth.nick));
    args.push(format!("-Dminedash.auth.uuid={}", auth.uuid));
    // JVM args: сначала родительские, потом NeoForge
    if let Some(parent) = &parent_vjson {
        if let Some(jvm) = &parent.arguments.as_ref().and_then(|a| a.jvm.as_ref()) {
            for a in jvm.iter() {
                push_argument(a, &vars, &mut args);
            }
        }
    }
    if let Some(jvm) = &vjson.arguments.as_ref().and_then(|a| a.jvm.as_ref()) {
        for a in jvm.iter() {
            push_argument(a, &vars, &mut args);
        }
    }
    // -cp для всех версий; NeoForge (BootstrapLauncher) использует его для поиска библиотек
    let has_module_path = args.iter().any(|a| a == "-p" || a == "--module-path");
    if !has_module_path && !args.contains(&classpath) {
        args.push("-cp".into());
        args.push(classpath);
    }
    args.push(vjson.mainClass.clone());
    // game args: сначала родительские, потом NeoForge
    if let Some(parent) = &parent_vjson {
        if let Some(game) = &parent.arguments.as_ref().and_then(|a| a.game.as_ref()) {
            for a in game.iter() {
                push_argument(a, &vars, &mut args);
            }
        }
    }
    if let Some(game) = &vjson.arguments.as_ref().and_then(|a| a.game.as_ref()) {
        for a in game.iter() {
            push_argument(a, &vars, &mut args);
        }
    }
    if settings.fullscreen {
        args.push("--fullscreen".into());
    } else {
        args.push("--width".into());
        args.push(settings.resolutionW.to_string());
        args.push("--height".into());
        args.push(settings.resolutionH.to_string());
    }
    // убираем --demo и quickPlay с пустыми значениями
    args.retain(|a| a != "--demo");
    let mut cleaned: Vec<String> = Vec::new();
    let mut skip_next = false;
    for i in 0..args.len() {
        if skip_next {
            skip_next = false;
            continue;
        }
        let a = &args[i];
        if a == "--quickPlayPath" || a == "--quickPlaySingleplayer" || a == "--quickPlayMultiplayer" || a == "--quickPlayRealms" {
            // пропускаем флаг и следующее пустое значение
            if i + 1 < args.len() && args[i + 1].is_empty() {
                skip_next = true;
            }
            continue;
        }
        cleaned.push(a.clone());
    }
    args = cleaned;
    // автоподключение к серверу отключено (сервер на VDS удалён)
    // if settings.autoJoin && !settings.serverAddress.trim().is_empty() {
    //     args.push("--server".into());
    //     args.push(settings.serverAddress.trim().into());
    //     args.push("--port".into());
    //     args.push("25565".into());
    // }
    // javaw.exe вместо java.exe — без консоли
    let java_exe = if java_exe.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default() == "java.exe" {
        java_exe.with_file_name("javaw.exe")
    } else {
        java_exe.to_path_buf()
    };
    let mut cmd = vec![java_exe.to_string_lossy().to_string()];
    cmd.extend(args);
    Ok((cmd, game_dir))
}

fn push_argument(a: &serde_json::Value, vars: &std::collections::HashMap<String, String>, out: &mut Vec<String>) {
    if let Some(s) = a.as_str() {
        out.push(substitute(s, vars));
    } else if let Some(obj) = a.as_object() {
        let rules_raw = obj.get("rules").cloned().unwrap_or(serde_json::Value::Null);
        let rules: Option<Vec<Rule>> = serde_json::from_value(rules_raw).ok();
        if !rules_allow(&rules) {
            return;
        }
        if let Some(v) = obj.get("value") {
            if let Some(s) = v.as_str() {
                out.push(substitute(s, vars));
            } else if let Some(arr) = v.as_array() {
                for item in arr {
                    if let Some(s) = item.as_str() {
                        out.push(substitute(s, vars));
                    }
                }
            }
        }
    }
}

fn dbg_log(msg: &str) {
    #[cfg(not(debug_assertions))]
    {
        let _ = msg;
        return;
    }
    #[cfg(debug_assertions)]
    {
    use std::io::Write;
    let path = std::env::temp_dir().join("minedash-debug.log");
    if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(&path) {
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        let _ = writeln!(f, "[{}] {}", ts, msg);
    }
    }
}

#[tauri::command]
fn game_launch(app: AppHandle, state: State<AppState>) -> LaunchResult {
    dbg_log("game_launch called");
    // уже запущено?
    {
        let mut running = state.game_running.lock().unwrap();
        if *running {
            return LaunchResult { ok: false, error: Some("Игра уже запущена".into()) };
        }
    }

    let settings = with_store(&state, |s| s.settings.clone());
    let auth = match with_store(&state, |s| s.auth.clone()) {
        Some(a) => a,
        None => {
            return LaunchResult { ok: false, error: Some("Сначала войдите в аккаунт MineDash.".into()) }
        }
    };
    dbg_log(&format!("auth ok, nick={}, authUrl={}", auth.nick, settings.authUrl));

    let root = game_root(&app);
    let app_h = app.clone();
    let version = with_store(&state, |s| s.lastVersion.clone());
    let auth_url = settings.authUrl.clone();

    std::thread::spawn(move || {
        let app = app_h;
        let result = (|| -> Result<(), String> {
            dbg_log("thread started: checking anti-cheat processes");
            check_blacklisted_processes()?;
            dbg_log("validating session");
            // проверка сессии на сервере
            let body = serde_json::json!({ "token": auth.token }).to_string();
            let validate = match http_json(&auth_url, "auth/validate", &body) {
                Ok(v) if v.get("ok").and_then(|o| o.as_bool()).unwrap_or(false) => v,
                _ => {
                    return Err("Сессия истекла. Войдите заново.".into());
                }
            };
            dbg_log("session validated");
            let mut auth = AuthState {
                token: auth.token,
                nick: validate.get("nick").and_then(|t| t.as_str()).unwrap_or("").into(),
                uuid: validate.get("uuid").and_then(|t| t.as_str()).unwrap_or("").into(),
            };
            // prepare launch
            dbg_log("preparing launch");
            let prep_body = serde_json::json!({ "token": auth.token }).to_string();
            let prepared = match http_json(&auth_url, "auth/launch", &prep_body) {
                Ok(v) if v.get("ok").and_then(|o| o.as_bool()).unwrap_or(false) => v,
                Ok(_) => return Err("Не удалось подготовить запуск. Войдите заново.".into()),
                Err(e) => return Err(e),
            };
            auth.uuid = prepared.get("uuid").and_then(|t| t.as_str()).unwrap_or("").into();
            auth.nick = prepared.get("nick").and_then(|t| t.as_str()).unwrap_or("").into();
            dbg_log("launch prepared, ensuring java");
            emit_progress(&app, "Проверка Java", 0, 5, 0);
            let java = ensure_java(&app, &root)?;
            emit_progress(&app, "Java готова", 1, 5, 0);
            std::thread::sleep(Duration::from_millis(200));
            dbg_log("java ok, ensuring game");
            emit_progress(&app, "Проверка клиента", 1, 5, 0);
            let _layout = ensure_game(&app, &root, &version)?;
            emit_progress(&app, "Клиент готов", 2, 5, 0);
            std::thread::sleep(Duration::from_millis(200));
            dbg_log("game ok, ensuring neoforge");
            emit_progress(&app, "Проверка NeoForge", 2, 5, 0);
            let nf_version = ensure_neoforge(&app, &root, &java, &version)?;
            emit_progress(&app, "NeoForge готов", 3, 5, 0);
            std::thread::sleep(Duration::from_millis(200));
            dbg_log(&format!("neoforge ok: {}", nf_version));
            let layout = game_layout(&root, &nf_version);
            emit_progress(&app, "Подготовка запуска", 3, 5, 0);
            dbg_log("building command");
            let (cmd, game_dir) = build_command(&layout, &java, &settings, &auth)?;
            emit_progress(&app, "Запуск игры", 4, 5, 0);
            std::thread::sleep(Duration::from_millis(300));
            dbg_log("command built, checking processes and spawning");
            check_blacklisted_processes()?;

            *app.state::<AppState>().game_running.lock().unwrap() = true;
            let _ = app.emit("game:state", "running");
            let _ = app.emit("game:progress", ProgressState { stage: "done".into(), file: None, done: 1, total: 1, speed: 0 });

            // Блокируем файлы модов на чтение (deny-write, deny-delete на уровне ядра Windows)
            let mut file_locks = lock_directory_files(&game_dir.join("mods"));
            file_locks.extend(lock_directory_files(&root.join("mods")));

            let program = &cmd[0];
            let rest = &cmd[1..];
            let mut child = std::process::Command::new(program)
                .args(rest)
                .env("MINEDASH_AUTH_TOKEN", &auth.token)
                .env("MINEDASH_AUTH_NICK", &auth.nick)
                .env("MINEDASH_AUTH_UUID", &auth.uuid)
                .current_dir(&game_dir)
                .stdout(std::process::Stdio::piped())
                .stderr(std::process::Stdio::piped())
                .spawn()
                .map_err(|e| e.to_string())?;

            let child_pid = child.id();
            let is_running = Arc::new(AtomicBool::new(true));
            let is_running_sentinel = is_running.clone();

            // Сохраняем снимок доверенных файлов в директории модов
            let mut expected_mods = std::collections::HashSet::new();
            if let Ok(entries) = fs::read_dir(&game_dir.join("mods")) {
                for entry in entries.flatten() {
                    expected_mods.insert(entry.file_name().to_string_lossy().to_string());
                }
            }

            // Sentinel watchdog поток: каждые 1200мс проверяет процессы и целостность папки
            let sentinel_game_dir = game_dir.clone();
            let sentinel_app = app.clone();
            std::thread::spawn(move || {
                dbg_log(&format!("Sentinel active watchdog started for PID {}", child_pid));
                let mods_path = sentinel_game_dir.join("mods");

                while is_running_sentinel.load(Ordering::SeqCst) {
                    std::thread::sleep(Duration::from_millis(1200));
                    if !is_running_sentinel.load(Ordering::SeqCst) {
                        break;
                    }

                    // 1. Проверка на запуск отладчиков и инжекторов во время работы игры
                    if let Err(msg) = check_blacklisted_processes() {
                        dbg_log(&format!("Sentinel ALERT: {}", msg));
                        kill_process_tree(child_pid);
                        let _ = sentinel_app.emit("game:error", format!("Защита MineDash: {}\nИгра экстренно остановлена.", msg));
                        break;
                    }

                    // 2. Проверка директории модов на подброс новых файлов или удаление существующих
                    if let Ok(entries) = fs::read_dir(&mods_path) {
                        let mut current_files = std::collections::HashSet::new();
                        for entry in entries.flatten() {
                            current_files.insert(entry.file_name().to_string_lossy().to_string());
                        }

                        let has_unauthorized = current_files.iter().any(|f| !expected_mods.contains(f));
                        let has_removed = expected_mods.iter().any(|f| !current_files.contains(f));

                        if has_unauthorized || has_removed {
                            dbg_log("Sentinel ALERT: Unauthorized file alteration in mods directory during runtime!");
                            kill_process_tree(child_pid);
                            let _ = sentinel_app.emit(
                                "game:error",
                                "Обнаружена попытка подмены или добавления модов во время игры!\nИгра закрыта системой безопасности MineDash.",
                            );
                            break;
                        }
                    }
                }
                dbg_log("Sentinel watchdog stopped.");
            });

            // читаем логи
            if let Some(out) = child.stdout.take() {
                let app = app.clone();
                std::thread::spawn(move || {
                    use std::io::BufRead;
                    let reader = std::io::BufReader::new(out);
                    for line in reader.lines().map_while(|l| l.ok()) {
                        if !line.trim().is_empty() {
                            let _ = app.emit("game:log", line);
                        }
                    }
                });
            }
            if let Some(err) = child.stderr.take() {
                let app = app.clone();
                std::thread::spawn(move || {
                    use std::io::BufRead;
                    let reader = std::io::BufReader::new(err);
                    for line in reader.lines().map_while(|l| l.ok()) {
                        if !line.trim().is_empty() {
                            let _ = app.emit("game:log", line);
                        }
                    }
                });
            }

            let app2 = app.clone();
            let is_running_waiter = is_running.clone();
            std::thread::spawn(move || {
                let status = child.wait();
                is_running_waiter.store(false, Ordering::SeqCst);
                *app2.state::<AppState>().game_running.lock().unwrap() = false;
                let _ = app2.emit("game:state", "idle");
                let code = status.ok().and_then(|s| s.code());
                let _ = app2.emit("game:exit", code);
                // Освобождаем дескрипторы блокировок файлов после закрытия игры
                drop(file_locks);
            });
            Ok(())
        })();

        if let Err(e) = result {
            dbg_log(&format!("launch error: {}", e));
            *app.state::<AppState>().game_running.lock().unwrap() = false;
            let _ = app.emit("game:state", "idle");
            let _ = app.emit("game:error", e);
        }
    });

    LaunchResult { ok: true, error: None }
}

fn with_store_any<T>(_s: State<AppState>, _f: impl FnOnce(&StoreShape) -> T) -> T {
    unimplemented!()
}

// ─────────────────────────────────────────────────────────── main

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let handle = app.handle().clone();
            extract_builtin_resources(&handle);
            let store = load_store_from(&store_file(&handle));
            app.manage(AppState {
                store: Mutex::new(store),
                game_running: Mutex::new(false),
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                let running = window
                    .state::<AppState>()
                    .game_running
                    .lock()
                    .map(|g| *g)
                    .unwrap_or(false);
                if running {
                    api.prevent_close();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            win_minimize,
            win_maximize,
            win_close,
            win_is_maximized,
            store_get,
            store_set_settings,
            skin_get,
            skin_set,
            skin_set_model,
            skin_reset,
            backgrounds_list,
            backgrounds_add,
            backgrounds_remove,
            background_get_data_url,
            app_version,
            app_pick_java,
            update_check,
            update_install,
            theme_get,
            theme_set,
            theme_reset,
            theme_export,
            theme_import,
            workshop_list,
            workshop_publish,
            workshop_install,
            workshop_uninstall,
            workshop_like,
            app_open_external,
            app_open_game_dir,
            app_set_last_server,
            auth_login,
            auth_restore,
            auth_logout,
            game_launch
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
