setup() {
    load '../tools/nexo-tools'
}

@test "nexo-tools help shows usage" {
    run ./tools/nexo-tools help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Nexo Tool Registry"* ]]
}

@test "nexo-tools unknown command fails" {
    run ./tools/nexo-tools nonexistent
    [ "$status" -eq 1 ]
    [[ "$output" == *"Comando desconocido"* ]]
}

@test "install.sh runs without errors" {
    run bash -n ./install.sh
    [ "$status" -eq 0 ]
}

@test "say.sh runs without syntax errors" {
    run bash -n ./voice/say.sh
    [ "$status" -eq 0 ]
}

@test "voice.sh runs without syntax errors" {
    run bash -n ./voice/voice.sh
    [ "$status" -eq 0 ]
}

@test "check-identity.sh has no syntax errors" {
    run bash -n ./core/identity/check-identity.sh
    [ "$status" -eq 0 ]
}

@test "verify-creator.sh has no syntax errors" {
    run bash -n ./core/identity/verify-creator.sh
    [ "$status" -eq 0 ]
}

@test "nexo-protect.sh has no syntax errors" {
    run bash -n ./core/identity/nexo-protect.sh
    [ "$status" -eq 0 ]
}

@test "nexo-verify-integrity.sh has no syntax errors" {
    run bash -n ./core/identity/nexo-verify-integrity.sh
    [ "$status" -eq 0 ]
}

@test "verify-secret.sh has no syntax errors" {
    run bash -n ./core/identity/verify-secret.sh
    [ "$status" -eq 0 ]
}

@test "temp-monitor.sh has no syntax errors" {
    run bash -n ./core/monitor/temp-monitor.sh
    [ "$status" -eq 0 ]
}

@test "temp-cancel.sh has no syntax errors" {
    run bash -n ./core/monitor/temp-cancel.sh
    [ "$status" -eq 0 ]
}

@test "limpiar has no syntax errors" {
    run bash -n ./core/system/limpiar
    [ "$status" -eq 0 ]
}

@test "nexo-memory has no syntax errors" {
    run bash -n ./memory/nexo-memory
    [ "$status" -eq 0 ]
}

@test "nexo-backup.sh has no syntax errors" {
    run bash -n ./backup/nexo-backup.sh
    [ "$status" -eq 0 ]
}

@test "nexo-restore.sh has no syntax errors" {
    run bash -n ./backup/nexo-restore.sh
    [ "$status" -eq 0 ]
}

@test "ejemplo.sh has no syntax errors" {
    run bash -n ./skills/ejemplo/scripts/ejemplo.sh
    [ "$status" -eq 0 ]
}

@test "all tools pass shellcheck" {
    skip "shellcheck might not be installed"
    for f in tools/nexo-*; do
        run shellcheck "$f"
        [ "$status" -eq 0 ]
    done
}

@test "say.sh --help prints usage" {
    run ./voice/say.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Uso"* ]]
}
