import io
import re

p = 'src/main.rs'
s = io.open(p, encoding='utf-8').read()

# 1. Settings: конфликт Default
s = re.sub(r"impl Default for Settings \{.*?\n\}\n\n", '', s, flags=re.S)

# 2. backgrounds_add
s = s.replace("""    let path = app
"""    let picked = app

# 3. virtual_links
s = s.replace('for (name, hash) in virtual_link {', 'for (name, hash) in &virtual_links {')

# 4. serde map_err
s = s.replace('serde_json::from_str(&raw)?',
              'serde_json::from_str(&raw).map_err(|e| e.to_string())?')
s = s.replace(
    'serde_json::from_str(&fs::read_to_string(&index_file).map_err(|e| e.to_string())?)?',
    'let raw = fs::read_to_string(&index_file).map_err(|e| e.to_string())?;\n        serde_json::from_str(&raw).map_err(|e| e.to_string())?')

# 5. client artifact Option
s = s.replace("""    tasks.push((
"""    let client_art = &vjson.downloads.client;
    tasks.push((
        client_art.url.clone().unwrap_or_default(),
        layout.client_jar.clone(),
        client_art.sha1.clone(),
        client_art.size,
    ));""")

# 6. iterators
s = s.replace('for a in jvm {', 'for a in jvm.iter() {')
s = s.replace('for a in game {', 'for a in game.iter() {')

# 7. download_pool: owned AppHandle + String stage
s = s.replace("""fn download_pool(
"""fn download_pool(
s = s.replace('emit_progress(app, stage, total, total, 0);',
              'emit_progress(&app, &stage, total, total, 0);')
s = s.replace('emit_progress(app, stage, d, total, speed);',
              'emit_progress(&app, &stage, d, total, speed);')
s = s.replace("""    std::thread::spawn(move || {
"""    let app_t = app.clone();
    let stage_t = stage.clone();
    std::thread::spawn(move || {
# убрать дублирующий clone app/stage в воркере
s = s.replace("""            let done = done.clone();
"""            let done = done.clone();
# вызовы
s = s.replace('download_pool(app, "libraries", tasks, 6)?;',
              'download_pool(app.clone(), "libraries".into(), tasks, 6)?;')
s = s.replace('download_pool(app, "assets", asset_tasks, 8)?;',
              'download_pool(app.clone(), "assets".into(), asset_tasks, 8)?;')
s = s.replace("""    download_pool(
"""    download_pool(

io.open(p, 'w', encoding='utf-8').write(s)
print('patched ok')
