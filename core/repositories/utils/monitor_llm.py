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
    model_name: Optional[str] = None
):
    """Registra las métricas en archivos CSV y JSON."""
    timestamp = time.time()
    metrics = {
        "task": task_name,
        "model": model_name or os.getenv('LLM_MODEL', 'unknown'),
        "elapsed_time_seconds": elapsed_time,
        "gpu_memory_delta_bytes": gpu_memory_delta,
        "gpu_memory_delta_mb": gpu_memory_delta / (1024 * 1024),
        "timestamp": timestamp,
        "human_readable_timestamp": datetime.fromtimestamp(timestamp).isoformat(),
    }
    if tokens_count is not None:
        metrics["tokens_count"] = tokens_count
    if tokens_per_second is not None:
        metrics["tokens_per_second"] = tokens_per_second

    # Asegurar directorios
    os.makedirs('logs', exist_ok=True)
    
    # Registro en CSV
    csv_path = "logs/metrics_log.csv"
    csv_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not csv_exists:
            # Escribir encabezados si el archivo no existía
            writer.writerow([
                "timestamp", "human_readable_timestamp", "task", "model", 
                "elapsed_time_seconds", "gpu_memory_delta_bytes", "gpu_memory_delta_mb",
                "tokens_count", "tokens_per_second"
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
            metrics.get("tokens_per_second", "")
        ])
    
    # Registro en JSON
    with open("logs/metrics_log.json", "a") as f:
        f.write(json.dumps(metrics) + "\n")

def monitor(task_name: Optional[str] = None):
    """
    Decorador para medir el tiempo de ejecución, la variación en el uso de GPU y calcular
    la cantidad de tokens generados y tokens por segundo. Permite especificar un nombre de tarea personalizado.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_task_name = task_name or func.__name__
            
            # Medir la memoria antes de la ejecución
            if torch.cuda.is_available():
                torch.cuda.synchronize()  # Asegura que se completen las operaciones previas
                mem_before = torch.cuda.memory_allocated(0)
            else:
                mem_before = 0
            
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error en tarea {current_task_name}: {e}")
                raise
            # Medir la memoria después de la ejecución
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                mem_after = torch.cuda.memory_allocated(0)
            else:
                mem_after = 0
            
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            gpu_memory_delta = mem_after - mem_before
            
            # Calcular el número de tokens a partir del resultado
            tokens_count = None
            tokens_per_second = None
            if isinstance(result, str):
                tokens_count = count_tokens(result)
            elif isinstance(result, dict):
                # Ajustar según la estructura esperada del diccionario
                if "text" in result and isinstance(result["text"], str):
                    tokens_count = count_tokens(result["text"])
                elif "summary" in result and isinstance(result["summary"], str):
                    tokens_count = count_tokens(result["summary"])
            if tokens_count is not None:
                tokens_per_second = tokens_count / elapsed_time if elapsed_time > 0 else 0
            
            # Registrar las métricas
            log_metrics(
                task_name=current_task_name, 
                elapsed_time=elapsed_time, 
                gpu_memory_delta=gpu_memory_delta,
                tokens_count=tokens_count,
                tokens_per_second=tokens_per_second
            )
            
            return result
        return wrapper
    return decorator

