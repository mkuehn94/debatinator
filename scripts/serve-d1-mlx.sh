#!/usr/bin/env bash
# macOS (Apple Silicon): mlx-vlm main with decision models. D1_MODEL = local MLX dir. Default D1_URL already points here.
exec python -m mlx_vlm server --decision-model "${D1_MODEL:?set D1_MODEL to an MLX d1 dir}" --host 127.0.0.1 --port "${PORT:-8095}"
