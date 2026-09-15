def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_seeded_questions_and_stats(client):
    stats = client.get("/api/stats/summary").json()
    assert stats["questions"] >= 10
    assert stats["categories"] == 12


def test_game_does_not_leak_answers(client):
    response = client.post("/api/games", json={"question_count": 5})
    assert response.status_code == 201, response.text
    game = response.json()
    assert len(game["questions"]) == 5
    serialized = str(game).lower()
    assert "bayeux tapestry" not in serialized or all(q["prompt"].lower().find("bayeux tapestry") == -1 for q in game["questions"])
    assert all("answers" not in q for q in game["questions"])


def test_grading_correct_answer(client):
    game = client.post("/api/games", json={"question_count": 10}).json()
    target = next(q for q in game["questions"] if "Saskatchewan" in q["prompt"])
    result = client.post(
        f"/api/games/{game['id']}/answer",
        json={"question_id": target["id"], "answers": {"main": "Regina"}},
    )
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["correct"] is True
    assert data["points_awarded"] == 1.0


def test_audio_upload_and_clip(client):
    import io
    import math
    import struct
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        frames = bytearray()
        for i in range(16000):
            sample = int(9000 * math.sin(2 * math.pi * 440 * i / 8000))
            frames.extend(struct.pack("<h", sample))
        wav.writeframes(frames)

    uploaded = client.post(
        "/api/media",
        files={"file": ("tone.wav", buf.getvalue(), "audio/wav")},
    )
    assert uploaded.status_code == 201, uploaded.text
    media_id = uploaded.json()["id"]

    clipped = client.post(
        f"/api/media/{media_id}/clip",
        json={"start_seconds": 0.2, "duration_seconds": 1.2, "normalize": True, "fade": True},
    )
    assert clipped.status_code == 201, clipped.text
    data = clipped.json()
    assert data["media_type"] == "audio"
    assert "/clips/" in data["path"]
