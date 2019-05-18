import psutil

__all__ = ["memory_usage"]



def memory_usage():
    mem_swap = psutil.swap_memory()
    mem_virt = psutil.virtual_memory()
    return {"virt_available":round(100-mem_virt.percent,2),"virt_used":mem_virt.percent,
            "swap_available":round(100-mem_swap.percent,2),"swap_used":mem_swap.percent}
    
def memory_size():
    return round(psutil.virtual_memory().total/1024/1000,2)






