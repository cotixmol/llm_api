def convert_request_outputs_to_dict(request_outputs):
    result = []
    
    for req_output in request_outputs:
        # Convert CompletionOutputs to dictionaries
        outputs_dicts = []
        for output in req_output.outputs:
            output_dict = {
                "index": output.index,
                "text": output.text,
                "token_ids": list(output.token_ids),  # Convert tuple to list
                "cumulative_logprob": output.cumulative_logprob,
                "logprobs": output.logprobs,
                "finish_reason": output.finish_reason,
                "stop_reason": output.stop_reason
            }
            outputs_dicts.append(output_dict)
            
        # Convert RequestMetrics to dictionary
        metrics_dict = {
            "arrival_time": req_output.metrics.arrival_time,
            "last_token_time": req_output.metrics.last_token_time,
            "first_scheduled_time": req_output.metrics.first_scheduled_time,
            "first_token_time": req_output.metrics.first_token_time,
            "time_in_queue": req_output.metrics.time_in_queue,
            "finished_time": req_output.metrics.finished_time,
            "scheduler_time": req_output.metrics.scheduler_time,
            "model_forward_time": req_output.metrics.model_forward_time,
            "model_execute_time": req_output.metrics.model_execute_time
        }
        
        # Convert RequestOutput to dictionary
        req_output_dict = {
            "request_id": req_output.request_id,
            "prompt": req_output.prompt,
            "prompt_token_ids": req_output.prompt_token_ids,
            "encoder_prompt": req_output.encoder_prompt,
            "encoder_prompt_token_ids": req_output.encoder_prompt_token_ids,
            "prompt_logprobs": req_output.prompt_logprobs,
            "outputs": outputs_dicts,
            "finished": req_output.finished,
            "metrics": metrics_dict,
            "lora_request": req_output.lora_request,
            "num_cached_tokens": req_output.num_cached_tokens,
            "multi_modal_placeholders": req_output.multi_modal_placeholders
        }
        
        result.append(req_output_dict)
    
    return result