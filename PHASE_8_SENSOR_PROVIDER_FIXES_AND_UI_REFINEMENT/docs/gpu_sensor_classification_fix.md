# GPU Sensor Classification Fix

Phase 8 classifies LibreHardwareMonitor GPU hardware types more broadly.

Recognized as GPU:
- `Gpu`
- `GpuNvidia`
- `GpuAmd`
- hardware type starting with `Gpu`
- hardware/name text containing NVIDIA, RTX, GeForce, AMD Radeon, or GPU

Normalized GPU keys include:
- `gpu_core_temp_c`
- `gpu_hotspot_temp_c`
- `gpu_memory_junction_temp_c`
- `gpu_core_clock_mhz`
- `gpu_memory_clock_mhz`
- `gpu_core_load_percent`
- `gpu_memory_load_percent`
- `gpu_package_power_w`
- `gpu_vram_used_mb`
- `gpu_vram_total_mb`
- `gpu_pcie_rx_bps`
- `gpu_pcie_tx_bps`

Impossible readings such as GPU Memory Junction at 255 C are marked `invalid_value`, not displayed as valid danger telemetry.
