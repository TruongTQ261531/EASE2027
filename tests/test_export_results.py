from ease_rtc.publish import sanitize


def test_export_removes_nested_network_identifiers_and_preserves_measurements():
    value = {
        "monotonic_ms": 250.0,
        "receiver_stats": [
            {"type": "certificate", "base64Certificate": "private-cert"},
            {
                "type": "local-candidate",
                "address": "internal",
                "ip": "internal",
                "port": 1234,
                "url": "turn:internal",
                "usernameFragment": "ephemeral",
                "id": "c1",
            },
            {
                "type": "transport",
                "iceLocalUsernameFragment": "ephemeral",
                "selectedCandidatePairId": "pair",
                "bytesReceived": 1000,
            },
            {"type": "inbound-rtp", "jitter": 0.02, "framesDecoded": 20},
        ],
    }
    public = sanitize(value)
    assert public["monotonic_ms"] == 250.0
    assert len(public["receiver_stats"]) == 3
    assert public["receiver_stats"][0] == {"type": "local-candidate", "id": "c1"}
    assert public["receiver_stats"][1]["bytesReceived"] == 1000
    assert public["receiver_stats"][2] == value["receiver_stats"][3]
    assert value["receiver_stats"][1]["address"] == "internal"
