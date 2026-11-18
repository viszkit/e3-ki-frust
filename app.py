"""Streamlit entry point for the local KI-Frust experiment."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from database import Database
from experiment import CONDITIONS, CONDITION_LABELS, RIDDLES, aid_is_available, is_correct
from providers import PROVIDERS, generate_reply, get_provider, test_connection
from settings import AppSettings, load_settings, masked_key, save_settings

APP_DIR = Path(__file__).resolve().parent
DATABASE_PATH = APP_DIR / "data" / "ki_frust.db"
SETTINGS_PATH = APP_DIR / ".streamlit" / "secrets.toml"
MAX_AI_MESSAGES_PER_RIDDLE = 5


@st.cache_resource
def get_database() -> Database:
    return Database(DATABASE_PATH)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_system_prompt(riddle) -> str:
    return f"""Du bist eine hilfreiche Assistenz in einem lokalen Logikrätsel-Test.
Antworte ausschließlich auf Fragen zum aktuellen Rätsel. Frage nicht nach persönlichen Daten.
Du darfst Lösungsstrategien, Hinweise und auf direkte Nachfrage auch die vollständige Lösung nennen.
Sei präzise und erkläre deine Schlussfolgerung knapp.

Aktuelles Rätsel: {riddle.title}
{riddle.prompt}

Antwortmöglichkeiten:
{chr(10).join(f'{index + 1}. {option}' for index, option in enumerate(riddle.options))}

Musterlösung: {riddle.options[riddle.correct_option]}
"""


def set_query(**values: str) -> None:
    st.query_params.clear()
    for key, value in values.items():
        st.query_params[key] = value


def read_settings() -> AppSettings:
    try:
        return load_settings(SETTINGS_PATH)
    except Exception as error:
        st.error(f"Die lokale Einstellungsdatei konnte nicht gelesen werden: {error}")
        st.stop()


def go_home_button() -> None:
    if st.button("Zur Startseite"):
        set_query(page="home")
        st.rerun()


def show_home() -> None:
    settings = read_settings()
    provider = get_provider(settings.active_provider)
    configured = settings.provider_settings(provider.id)

    st.title("KI-Frust: Logikrätsel-Test")
    st.write(
        "In diesem lokalen Prototyp bearbeiten Sie acht Logikrätsel. "
        "Je nach zufälliger Bedingung stehen in den ersten vier Rätseln unterschiedliche Hilfen bereit."
    )
    st.info(
        "Die App speichert nur anonyme Antworten, Bearbeitungszeiten, Frustwerte und die Nutzung "
        "von Hilfen in einer lokalen SQLite-Datei. API-Keys und Chatnachrichten werden nicht gespeichert."
    )

    st.subheader("Aktive KI-Konfiguration")
    if configured.api_key:
        st.success(f"{provider.label} · `{configured.model}` · Key gespeichert ({masked_key(configured.api_key)})")
    else:
        st.warning(f"{provider.label} · `{configured.model}` · Noch kein API-Key gespeichert")

    test_column, dashboard_column, settings_column = st.columns(3)
    with test_column:
        if st.button("Test starten", type="primary", use_container_width=True):
            if not configured.api_key:
                st.error("Bitte hinterlegen Sie zuerst einen getesteten API-Key in den Einstellungen.")
                return
            session_id = secrets.token_urlsafe(18)
            condition = secrets.choice(CONDITIONS)
            get_database().create_session(session_id, condition, provider.id, configured.model)
            set_query(page="test", session=session_id)
            st.rerun()
    with dashboard_column:
        if st.button("Dashboard", use_container_width=True):
            set_query(page="dashboard")
            st.rerun()
    with settings_column:
        if st.button("⚙ Einstellungen", use_container_width=True):
            set_query(page="settings")
            st.rerun()


def show_settings() -> None:
    settings = read_settings()
    st.title("⚙ Einstellungen")
    st.caption(
        "API-Keys werden nur lokal in `.streamlit/secrets.toml` gespeichert. "
        "Diese Datei wird nicht über Git veröffentlicht."
    )

    provider_id = st.selectbox(
        "KI-Anbieter",
        options=list(PROVIDERS),
        index=list(PROVIDERS).index(settings.active_provider),
        format_func=lambda value: PROVIDERS[value].label,
    )
    provider = get_provider(provider_id)
    configured = settings.provider_settings(provider_id)
    if provider.free_tier_badge:
        st.badge(provider.free_tier_badge, color="green")

    model_options = [*provider.model_options, "Eigenes Modell …"]
    model_index = model_options.index(configured.model) if configured.model in provider.model_options else len(model_options) - 1
    model_choice = st.selectbox("Modell", model_options, index=model_index)
    if model_choice == "Eigenes Modell …":
        selected_model = st.text_input("Eigener Modellname", value=configured.model)
    else:
        selected_model = model_choice

    st.write(f"Gespeicherter Key: `{masked_key(configured.api_key)}`")
    replacement_key = st.text_input(
        f"{provider.key_label} ändern",
        type="password",
        placeholder="Leer lassen, um den gespeicherten Key zu behalten",
    )
    st.caption("Eine Verbindung wird vor dem Speichern mit einer kurzen echten Modellanfrage getestet.")

    save_column, delete_column, back_column = st.columns(3)
    with save_column:
        if st.button("Verbindung testen und speichern", type="primary", use_container_width=True):
            candidate_key = replacement_key.strip() or configured.api_key
            candidate_model = selected_model.strip()
            if not candidate_key:
                st.error("Bitte geben Sie einen API-Key ein.")
                return
            if not candidate_model:
                st.error("Bitte wählen oder geben Sie einen Modellnamen ein.")
                return
            with st.spinner("Verbindung wird getestet …"):
                successful, message = test_connection(provider.id, candidate_key, candidate_model)
            if not successful:
                st.error(message)
                return
            configured.api_key = candidate_key
            configured.model = candidate_model
            settings.active_provider = provider.id
            save_settings(settings, SETTINGS_PATH)
            st.success(message)
    with delete_column:
        if st.button("Key löschen", use_container_width=True, disabled=not configured.api_key):
            configured.api_key = ""
            save_settings(settings, SETTINGS_PATH)
            st.success(f"Der gespeicherte {provider.label}-Key wurde lokal entfernt.")
            st.rerun()
    with back_column:
        go_home_button()


def show_static_help(session_id: str, riddle_number: int, riddle, attempt: dict) -> None:
    st.subheader("Hilfe verfügbar")
    st.warning("**Stecken Sie fest?** Zusätzliche Hinweise können Ihnen beim Weiterdenken helfen.")
    hint_clicks = attempt["hint_clicks"]
    labels = ("Ersten Hinweis nutzen", "Konkreteren Hinweis anzeigen", "Vollständige Lösung anzeigen")
    for hint_index in range(hint_clicks):
        label = "Vollständige Lösung" if hint_index == 2 else f"Hinweis {hint_index + 1}"
        st.info(f"**{label}:** {riddle.hints[hint_index]}")
    if hint_clicks < 3:
        if st.button(labels[hint_clicks], type="primary", use_container_width=True, key=f"hint-{riddle_number}"):
            get_database().increment_hint(session_id, riddle_number)
            st.rerun()
    else:
        st.caption("Alle drei Hilfestufen wurden angezeigt.")


def show_ai_chat(session_id: str, riddle_number: int, riddle, attempt: dict, provider_id: str, model: str) -> None:
    settings = read_settings()
    provider = get_provider(provider_id)
    api_key = settings.provider_settings(provider.id).api_key
    st.subheader("KI-Chat")
    st.caption(f"{provider.label} · `{model}` · Direkte Lösungsfragen sind erlaubt.")
    if not api_key:
        st.error("Der für diese Sitzung benötigte API-Key wurde in den Einstellungen entfernt.")
        return

    history_key = f"chat_history_{session_id}_{riddle_number}"
    history: list[dict[str, str]] = st.session_state.setdefault(history_key, [])
    for message in history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if attempt["ai_message_count"] >= MAX_AI_MESSAGES_PER_RIDDLE:
        st.caption(f"Das Nachrichtenlimit von {MAX_AI_MESSAGES_PER_RIDDLE} pro Rätsel ist erreicht.")
        return

    question = st.chat_input("Frage zum aktuellen Rätsel", key=f"chat-input-{riddle_number}")
    if not question:
        return
    history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("KI antwortet …"):
            try:
                reply = generate_reply(provider_id, api_key, model, make_system_prompt(riddle), history[:-1], question)
            except Exception as error:
                st.error(str(error))
                history.pop()
                return
        st.write(reply)
    history.append({"role": "assistant", "content": reply})
    get_database().increment_ai_message(session_id, riddle_number)


def show_no_help() -> None:
    st.subheader("Unterstützung")
    st.info("Für dieses Rätsel steht keine zusätzliche Unterstützung zur Verfügung.")


def show_test(session_id: str) -> None:
    database = get_database()
    session = database.get_session(session_id)
    if not session:
        st.error("Diese Testsitzung wurde nicht gefunden.")
        go_home_button()
        return
    if session["completed_at"]:
        st.success("Vielen Dank. Der Test wurde lokal gespeichert.")
        st.write("Die Ergebnisse können im Dashboard dieser lokalen App angesehen werden.")
        first, second = st.columns(2)
        with first:
            if st.button("Zum Dashboard", type="primary"):
                set_query(page="dashboard")
                st.rerun()
        with second:
            go_home_button()
        return

    riddle_number = session["current_riddle"]
    riddle = RIDDLES[riddle_number - 1]
    has_aid = aid_is_available(session["condition"], riddle_number)
    attempt = database.get_or_create_attempt(session_id, riddle_number, has_aid)
    puzzle_column, help_column = st.columns([2, 1], gap="large")

    with puzzle_column:
        st.title("KI-Frust: Logikrätsel-Test")
        st.progress((riddle_number - 1) / len(RIDDLES), text=f"Rätsel {riddle_number} von {len(RIDDLES)}")
        st.subheader(riddle.title)
        st.write(riddle.prompt)
        shown_at = datetime.fromisoformat(attempt["shown_at"])
        elapsed = max(0, int((utc_now() - shown_at).total_seconds()))
        st.caption(f"Zeitmessung läuft seit {elapsed // 60}:{elapsed % 60:02d} Minuten.")
        st.divider()
        choice = st.radio(
            "Welche Antwort ist richtig?",
            options=list(range(len(riddle.options))),
            index=None,
            format_func=lambda index: riddle.options[index],
            key=f"answer-{session_id}-{riddle_number}",
        )
        st.markdown("#### Frustbewertung")
        frustration = st.radio(
            "Wie frustrierend war dieses Rätsel für Sie?",
            options=[1, 2, 3, 4, 5],
            index=None,
            format_func=lambda value: {
                1: "1 – gar nicht frustrierend",
                2: "2 – eher wenig frustrierend",
                3: "3 – teils/teils",
                4: "4 – eher frustrierend",
                5: "5 – sehr frustrierend",
            }[value],
            key=f"frustration-{session_id}-{riddle_number}",
        )
        if st.button("Antwort speichern und weiter", type="primary"):
            if choice is None or frustration is None:
                st.warning("Bitte wählen Sie eine Antwort und einen Frustwert aus.")
                return
            database.submit_attempt(session_id, riddle_number, choice, is_correct(riddle, choice), frustration)
            st.rerun()

    with help_column:
        with st.container(border=True):
            if has_aid and session["condition"] == "statische_hilfe":
                show_static_help(session_id, riddle_number, riddle, attempt)
            elif has_aid and session["condition"] == "ki_chat":
                show_ai_chat(session_id, riddle_number, riddle, attempt, session["provider"], session["model"])
            else:
                show_no_help()


def show_dashboard() -> None:
    st.title("Lokales Dashboard")
    st.caption("Es werden nur abgeschlossene Tests aus dieser lokalen SQLite-Datei ausgewertet.")
    database = get_database()
    rows = database.dashboard_rows()
    counts = pd.DataFrame(database.completed_session_counts())
    if not rows:
        st.info("Es liegen noch keine abgeschlossenen Tests in dieser lokalen Installation vor.")
        go_home_button()
        return

    data = pd.DataFrame(rows)
    data["block"] = data["riddle_number"].map(lambda number: "Rätsel 1–4" if number <= 4 else "Rätsel 5–8")
    data["condition_label"] = data["condition"].map(CONDITION_LABELS)
    st.subheader("Abgeschlossene Tests nach Startbedingung")
    all_conditions = pd.DataFrame({"condition": list(CONDITIONS)})
    count_display = all_conditions.merge(counts, on="condition", how="left").fillna({"sessions": 0})
    count_display["Startbedingung"] = count_display["condition"].map(CONDITION_LABELS)
    count_display["Abgeschlossene Tests"] = count_display["sessions"].astype(int)
    st.dataframe(count_display[["Startbedingung", "Abgeschlossene Tests"]], hide_index=True, use_container_width=True)

    metrics = data.groupby(["condition_label", "block"], observed=True).agg(
        Antworten=("is_correct", "size"),
        Bearbeitungszeit_Sekunden=("duration_seconds", "mean"),
        Lösungsquote=("is_correct", "mean"),
        Frustwert=("frustration", "mean"),
    ).reset_index()
    metrics["Bearbeitungszeit (Sek.)"] = metrics["Bearbeitungszeit_Sekunden"].round(1)
    metrics["Lösungsquote (%)"] = (metrics["Lösungsquote"] * 100).round(1)
    metrics["Frustwert (1–5)"] = metrics["Frustwert"].round(2)
    st.subheader("Kennzahlen nach Bedingung und Block")
    st.dataframe(
        metrics[["condition_label", "block", "Antworten", "Bearbeitungszeit (Sek.)", "Lösungsquote (%)", "Frustwert (1–5)"]]
        .rename(columns={"condition_label": "Startbedingung", "block": "Rätselblock"}),
        hide_index=True,
        use_container_width=True,
    )
    st.subheader("Vergleich der Bearbeitungszeit")
    st.bar_chart(metrics.pivot(index="condition_label", columns="block", values="Bearbeitungszeit (Sek.)"))

    st.subheader("Nutzung verfügbarer Hilfen (Rätsel 1–4)")
    usage = data[data["riddle_number"] <= 4]
    static_usage = usage[usage["condition"] == "statische_hilfe"]["hint_clicks"]
    ai_usage = usage[usage["condition"] == "ki_chat"]["ai_message_count"]
    help_left, help_right = st.columns(2)
    help_left.metric("Ø Hinweise pro statischem Rätsel", f"{static_usage.mean():.2f}" if not static_usage.empty else "–")
    help_right.metric("Ø KI-Nachrichten pro KI-Rätsel", f"{ai_usage.mean():.2f}" if not ai_usage.empty else "–")

    st.subheader("Verwendete Anbieter und Modelle")
    contexts = data[["session_id", "provider", "model"]].drop_duplicates().groupby(["provider", "model"]).size().reset_index(name="Tests")
    st.dataframe(contexts.rename(columns={"provider": "Anbieter", "model": "Modell"}), hide_index=True, use_container_width=True)
    go_home_button()


def main() -> None:
    st.set_page_config(page_title="KI-Frust", page_icon="🧩", layout="wide")
    page = st.query_params.get("page", "home")
    if page == "settings":
        show_settings()
    elif page == "dashboard":
        show_dashboard()
    elif page == "test":
        session_id = st.query_params.get("session")
        if session_id:
            show_test(session_id)
        else:
            show_home()
    else:
        show_home()


if __name__ == "__main__":
    main()
