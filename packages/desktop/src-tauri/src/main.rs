use tauri::{WebviewUrl, WebviewWindowBuilder};

fn main() {
    // Only a real hosted HTTPS URL is valid. The web app is never duplicated.
    let remote = std::env::var("BGWQ_WEB_URL")
        .expect("BGWQ_WEB_URL must point to the reviewed hosted HTTPS application");
    let url = url::Url::parse(&remote).expect("BGWQ_WEB_URL is not a valid absolute URL");
    assert!(
        url.scheme() == "https"
            && url.host_str().is_some()
            && url.username().is_empty()
            && url.password().is_none()
            && url.fragment().is_none(),
        "BGWQ_WEB_URL must be an HTTPS origin without credentials or fragments"
    );
    assert!(
        url.path() == "/" && url.query().is_none(),
        "BGWQ_WEB_URL must be the origin, not a nested route or query"
    );

    tauri::Builder::default()
        .setup(move |app| {
            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url.clone()))
                .title("BoardGamesWithQuests")
                .inner_size(1080.0, 720.0)
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("unable to run BoardGamesWithQuests desktop wrapper");
}
