# Native

One Tauri 2 shell for Windows, Linux, macOS, Android and iOS. It navigates
straight to `https://boardgameswithquests-web.vercel.app`, the **same** React
app used by the browser. No embedded frontend copy, Python runtime, privileged
JavaScript bridge or separate game implementation is shipped.

```sh
bun install
bun run icon
bun tauri dev
bun tauri build
```

The icon generator creates `src-tauri/icons/*.png`, `.ico`, `.icns` from
tracked SVG. Native builders/CI must run it before compilation. For Android,
install Java/Android SDK/NDK then run `bun tauri android init` and
`bun tauri android build --apk`. For iOS, use a macOS/Xcode runner, install
CocoaPods and run `bun tauri ios init` followed by a provisioning-backed build.

The native app **requires network access**. Remote site updates change the
app's web behavior without a native recompile. Distribution readiness is
separate from an unsigned build: iOS requires Apple signing and provisioning;
Play/App Store approval is not provided by CI.
