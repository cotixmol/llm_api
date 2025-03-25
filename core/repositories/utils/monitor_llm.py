import time
import csv
import json
import logging
import torch
from functools import wraps
from typing import Optional, Any
import os
from datetime import datetime

def count_tokens(text: str) -> int:
    return len(text.split())

def log_metrics(
    task_name: str, 
    elapsed_time: float, 
    gpu_memory_delta: int, 
    tokens_count: Optional[int] = None, 
    tokens_per_second: Optional[float] = None,
    model_name: Optional[str] = None,
    prompt: Optional[Any] = None,
    output: Optional[Any] = None
):
    """Registra las métricas en archivos CSV y JSON con nombres únicos."""
    timestamp = time.time()
    human_ts = datetime.fromtimestamp(timestamp).isoformat()
    # Genera un identificador único basado en fecha y microsegundos
    unique_id = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S_%f")
    
    metrics = {
        "task": task_name,
        "model": model_name or os.getenv('LLM_MODEL', 'unknown'),
        "elapsed_time_seconds": elapsed_time,
        "gpu_memory_delta_bytes": gpu_memory_delta,
        "gpu_memory_delta_mb": gpu_memory_delta / (1024 * 1024),
        "timestamp": timestamp,
        "human_readable_timestamp": human_ts,
    }
    if tokens_count is not None:
        metrics["tokens_count"] = tokens_count
    if tokens_per_second is not None:
        metrics["tokens_per_second"] = tokens_per_second
    if prompt is not None:
        metrics["prompt"] = prompt
    if output is not None:
        metrics["output"] = output

    # Asegurar directorio logs
    os.makedirs('logs', exist_ok=True)
    
    # Definir rutas únicas para los archivos usando el unique_id
    csv_path = f"logs/metrics_log_{unique_id}.csv"
    json_path = f"logs/metrics_log_{unique_id}.json"
    
    # Guardar en CSV
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "human_readable_timestamp", "task", "model", 
            "elapsed_time_seconds", "gpu_memory_delta_bytes", "gpu_memory_delta_mb",
            "tokens_count", "tokens_per_second", "prompt", "output"
        ])
        writer.writerow([
            metrics["timestamp"],
            metrics["human_readable_timestamp"],
            metrics["task"],
            metrics["model"],
            metrics["elapsed_time_seconds"],
            metrics["gpu_memory_delta_bytes"],
            metrics["gpu_memory_delta_mb"],
            metrics.get("tokens_count", ""),
            metrics.get("tokens_per_second", ""),
            metrics.get("prompt", ""),
            metrics.get("output", "")
        ])
    
    # Guardar en JSON (una línea por registro)
    with open(json_path, "w") as f:
        f.write(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n")

def monitor(task_name: Optional[str] = None):
    """
    Decorador para medir el tiempo de ejecución, la variación en el uso de GPU y calcular
    la cantidad de tokens generados y tokens por segundo. Además, registra el prompt y el output.
    Permite especificar un nombre de tarea personalizado.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_task_name = task_name or func.__name__
            
            # Capturamos el prompt a partir de los argumentos: se asume que es el segundo argumento (después de self)
            prompt_value = None
            if len(args) > 1:
                prompt_value = args[1]
            elif "prompt" in kwargs:
                prompt_value = kwargs["prompt"]
            
            if torch.cuda.is_available():
                torch.cuda.synchronize()  # Sincroniza para medición precisa
                mem_before = torch.cuda.memory_allocated(0)
            else:
                mem_before = 0
            
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error en tarea {current_task_name}: {e}")
                raise
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                mem_after = torch.cuda.memory_allocated(0)
            else:
                mem_after = 0
            
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            gpu_memory_delta = mem_after - mem_before
            
            # Procesar el output para contar tokens y obtener el texto relevante.
            tokens_count = None
            tokens_per_second = None
            output_text = None
            if isinstance(result, str):
                output_text = result
                tokens_count = count_tokens(result)
            elif isinstance(result, dict):
                if "text" in result and isinstance(result["text"], str):
                    output_text = result["text"]
                    tokens_count = count_tokens(result["text"])
                elif "summary" in result and isinstance(result["summary"], str):
                    output_text = result["summary"]
                    tokens_count = count_tokens(result["summary"])
            if tokens_count is not None:
                tokens_per_second = tokens_count / elapsed_time if elapsed_time > 0 else 0
            
            # Registrar las métricas, incluyendo prompt y output
            log_metrics(
                task_name=current_task_name, 
                elapsed_time=elapsed_time, 
                gpu_memory_delta=gpu_memory_delta,
                tokens_count=tokens_count,
                tokens_per_second=tokens_per_second,
                prompt=prompt_value,
                output=output_text
            )
            
            return result
        return wrapper
    return decorator
