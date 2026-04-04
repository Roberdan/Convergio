//! HTTP routes for voice — TTS, STT, intent, status.

use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use serde::Deserialize;
use serde_json::json;
use std::sync::{Arc, Mutex};

use crate::tts::TtsEngine;

/// Shared state for voice routes.
#[derive(Clone)]
pub struct VoiceState {
    pub tts: Arc<Mutex<TtsEngine>>,
}

/// Build all voice routes.
pub fn voice_routes(state: VoiceState) -> Router {
    Router::new()
        .route("/api/voice/status", get(voice_status))
        .route("/api/voice/speak", post(speak))
        .route("/api/voice/intent", post(extract_intent))
        .with_state(state)
}

async fn voice_status(
    axum::extract::State(st): axum::extract::State<VoiceState>,
) -> impl IntoResponse {
    let backend = st
        .tts
        .lock()
        .map(|e| e.backend().display_name().to_string())
        .unwrap_or_else(|_| "unknown".into());
    ok(json!({"status": "ok", "tts_backend": backend}))
}

#[derive(Deserialize)]
struct SpeakReq {
    text: String,
    #[serde(default = "default_locale")]
    locale: String,
}

fn default_locale() -> String {
    "en-US".into()
}

async fn speak(
    axum::extract::State(st): axum::extract::State<VoiceState>,
    Json(r): Json<SpeakReq>,
) -> impl IntoResponse {
    let result = st
        .tts
        .lock()
        .map_err(err)
        .and_then(|mut engine| engine.speak(&r.text, &r.locale).map_err(err));
    match result {
        Ok(audio) => Ok((StatusCode::OK, [("content-type", "audio/wav")], audio)),
        Err(e) => Err(e),
    }
}

#[derive(Deserialize)]
struct IntentReq {
    text: String,
}

async fn extract_intent(Json(r): Json<IntentReq>) -> impl IntoResponse {
    let intent = crate::intent::extract_intent(&r.text).map_err(err)?;
    ok(json!(intent))
}

fn err(e: impl std::fmt::Display) -> (StatusCode, String) {
    (StatusCode::INTERNAL_SERVER_ERROR, e.to_string())
}

fn ok(v: serde_json::Value) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    Ok(Json(v))
}
