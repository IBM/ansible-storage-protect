
# offerings_metadata = {
#     "oc": {
#         "profile": "IBM Spectrum Protect",
#         "id": "com.tivoli.dsm.gui.offering",
#         "features": "com.tivoli.dsm.gui.main_asm,com.ibm.java.jre"
#     },
#     "server": {
#         "profile": "IBM Spectrum Protect",
#         "id": "com.tivoli.dsm.server",
#         "features": "com.tivoli.dsm.server.main,com.tivoli.dsm.gskit,com.tivoli.dsm.clientapi,com.ibm.java.jre"
#     },
#     "stagent": {
#         "profile": "IBM Spectrum Protect",
#         "id": "com.tivoli.dsm.stagent",
#         "features": "com.tivoli.dsm.stagent.main,com.tivoli.dsm.gskit"
#     },
#     "devices": {
#         "profile": "IBM Spectrum Protect",
#         "id": "com.tivoli.dsm.devices",
#         "features": "com.tivoli.dsm.devices.main"
#     },
#     "ossm": {
#         "profile": "IBM Spectrum Protect",
#         "id": "com.tivoli.dsm.ossm",
#         "features": "com.tivoli.dsm.ossm.main,com.tivoli.dsm.gskit"
#     }
# }


offerings_metadata = {
    "server": {
        "id": "com.tivoli.dsm.server",
        "profile": "IBM Storage Protect",
        "features": "com.tivoli.dsm.server.main,com.tivoli.dsm.gskit,com.tivoli.dsm.clientapi,com.ibm.java.jre",
        "installFixes": "none",
    },
    "stagent": {
        "id": "com.tivoli.dsm.stagent",
        "profile": "IBM Spectrum Protect",
        "features": "com.tivoli.dsm.stagent.main,com.tivoli.dsm.gskit",
        "installFixes": "none",
    },
    "devices": {
        "id": "com.tivoli.dsm.devices",
        "profile": "IBM Spectrum Protect",
        "features": "com.tivoli.dsm.devices.main",
        "installFixes": "none",
    },
    "oc": {
        "id": "com.tivoli.dsm.gui.offering",
        "profile": "IBM Spectrum Protect",
        "features": "com.tivoli.dsm.gui.main_asm,com.ibm.java.jre",
        "installFixes": "none",
    },
    "ossm": {
        "id": "com.tivoli.dsm.ossm",
        "profile": "IBM Spectrum Protect",
        "features": "com.tivoli.dsm.ossm.main,com.tivoli.dsm.gskit",
        "installFixes": "none",
    },
    "license": {
        "id": "com.tivoli.dsm.license",
        "profile": "IBM Spectrum Protect",
        "features": "com.tivoli.dsm.license.main",
        "installFixes": "none",
    }
}

preferences = {
    "com.ibm.cic.common.core.preferences.connectTimeout": "30",
    "com.ibm.cic.common.core.preferences.readTimeout": "45",
    "com.ibm.cic.common.core.preferences.downloadAutoRetryCount": "0",
    "offering.service.repositories.areUsed": "false",
    "com.ibm.cic.common.core.preferences.ssl.nonsecureMode": "false",
    "com.ibm.cic.common.core.preferences.http.disablePreemptiveAuthentication": "false",
    "http.ntlm.auth.kind": "NTLM",
    "http.ntlm.auth.enableIntegrated.win32": "true",
    "com.ibm.cic.common.core.preferences.preserveDownloadedArtifacts": "false",
    "com.ibm.cic.common.core.preferences.keepFetchedFiles": "false",
    "PassportAdvantageIsEnabled": "false",
    "com.ibm.cic.common.core.preferences.searchForUpdates": "false",
    "com.ibm.cic.agent.ui.displayInternalVersion": "false",
    "com.ibm.cic.common.sharedUI.showErrorLog": "true",
    "com.ibm.cic.common.sharedUI.showWarningLog": "true",
    "com.ibm.cic.common.sharedUI.showNoteLog": "true",
}