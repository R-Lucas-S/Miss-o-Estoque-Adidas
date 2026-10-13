def build_result(level, scoring, quiz, started_at, now, **extra):
    """Cria um resumo flexivel da tentativa para a tela de resultados."""
    correct = scoring.correct_deliveries
    total_checks = correct + scoring.errors
    accuracy = round(correct / total_checks * 100) if total_checks else 100
    result = {
        "level": level,
        "completed": True,
        "score": scoring.score,
        "accuracy": accuracy,
        "errors": scoring.errors,
        "max_combo": scoring.max_combo,
        "quiz_correct": quiz.score,
        "quiz_total": len(quiz.questions),
        "objectives_completed": correct,
        "elapsed_seconds": max(0, (now - started_at) // 1000),
    }
    result.update(extra)
    return result
