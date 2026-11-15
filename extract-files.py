#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from camera.gpu_layout import fix_gpu_layout

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'device/motorola/bangkk',
    'device/motorola/sm6375-common',
    'hardware/motorola',
    'hardware/qcom-caf/sm6375-6.1',
    'vendor/motorola/sm6375-common',
]

def thermal_engine_fixup():
    # The shared Blair DT registers the pm7250b charger ADC channel as
    # chg-skin-therm (holi-pm7250b.dtsi) before bangkk's chg_therm zone, so
    # chg_therm never appears on Linux 6.1. thermal-engine-v2 names its CPU
    # frequency devices cpu-cluster%d, so the v1-era cpu0 and cpu6 actions
    # match nothing and both CPU rules get rejected.
    return (
        blob_fixup()
        .regex_replace(r'\bchg_therm\b', 'chg-skin-therm')
        .regex_replace(r'\bcpu0\b', 'cpu-cluster0')
        .regex_replace(r'\bcpu6\b', 'cpu-cluster1')
    )


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
}

blob_fixups: blob_fixups_user_type = {
    'vendor/lib64/camera/components/com.qti.node.gpu.so': blob_fixup()
        .call(fix_gpu_layout),
    (
        'vendor/lib64/camera/components/com.mot.node.c2d.so',
        'vendor/lib64/camera/components/com.qti.node.dewarp.so',
        'vendor/lib64/camera/components/com.vidhance.node.ica.so',
        'vendor/lib64/camera/components/com.vidhance.node.processing.so',
    ): blob_fixup()
        .replace_needed('libui.so', 'libui-v34.so'),
    'vendor/lib64/hw/camera.qcom.so': blob_fixup()
        .replace_needed('libsnsapi.so', 'libsnsapi-stock.so'),
    # Linux 6.1 has no /dev/ion; the common shim serves these from DMA-BUF heaps.
    (
        'vendor/lib64/libacdbloader.so',
        'vendor/lib64/libets_teeclient_v3.so',
    ): blob_fixup()
        .replace_needed('libion.so', 'libion_qsecom_shim.so'),
    'vendor/lib64/libBSTSWAD.so': blob_fixup()
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_lock')
        .clear_symbol_version('AHardwareBuffer_lockPlanes')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock'),
    'vendor/lib64/libmot_chi_desktop_helper.so': blob_fixup()
        .add_needed('libgui_buffer_shim_vendor.so'),
    'vendor/etc/thermal-engine-bangkk.conf': thermal_engine_fixup(),
    'vendor/etc/thermal-engine-bangkk-camera.conf': thermal_engine_fixup(),
    'vendor/etc/thermal-engine-bangkk-game-normal.conf': thermal_engine_fixup(),
    'vendor/etc/thermal-engine-bangkk-game-perf.conf': thermal_engine_fixup(),
}  # fmt: skip

module = ExtractUtilsModule(
    'bangkk',
    'motorola',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
    add_firmware_proprietary_file=False,
)

if __name__ == '__main__':
    utils = ExtractUtils.device_with_common(
        module, 'sm6375-common', module.vendor
    )
    utils.run()
