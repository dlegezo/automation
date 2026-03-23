rule muddywater_launcher_dinodance {
	meta:
		author = "Google Threat Intelligence Group (GTIG)"
        date = "2026-02-17"
	strings:
		$str1 = ".env.get(\"USERNAME\")" base64
		$str2 = ".env.get(\"USER\")" base64
		$str3 = ".hostname()" base64
		$str4 = ".systemMemoryInfo()" base64
		$str5 = ".osRelease()" base64
		$str6 = ".listen" base64
		$str7 = "hostname:" base64
		$str8 = "transport:" base64
		$str9 = ".Command" base64
		$str10 = "127.0.0.1" base64
		$str11 = "tcp" base64
	condition:
		uint16(0) != 0x5A4D and 8 of them and filesize < 10KB
}

rule muddywater_backdoor_dinodance {
	meta:
		author = "Google Threat Intelligence Group (GTIG)"
        date = "2026-02-17"
	strings:
		$str1 = "Ps1File"
		$str2 = "VbsFile"
		$str3 = "Installation Database"
		$str4 = "Windows Installer XML Toolset"
		$str5 = "_ValidationTable"
	condition:
		uint32(0) == 0xE011CFD0 and all of them
}

rule muddywater_dropper_dinodance_vbs {
	meta:
		author = "Google Threat Intelligence Group (GTIG)"
        date = "2026-02-17"
	strings:
		$str1 = "VBS launcher - runs PowerShell script hidden"
		$str2 = "WScript.Shell"
		$str3 = "Scripting.FileSystemObject"
		$str4 = "WScript.ScriptFullName"
		$str5 = ".BuildPath"
		$str6 = ".GetParentFolderName"
		$str7 = ".Run \"powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File"
	condition:
		uint16(0) != 0x5A4D and all of them and filesize < 10KB
}

rule muddywater_ateraagent
{
  meta:
    description = "Detect Atera Agent abused by MuddyWater"
    references = "TRR240402"
    hash = "9b49d6640f5f0f1d68f649252a96052f1d2e0822feadd7ebe3ab6a3cadd75985"
    date = "2024-04-17"
    author = "HarfangLab"
    context = "file"
  strings:
    $s1 = "COMPANYID001Q3000009snPyIAIACCOUNTID"
    $s2 = "COMPANYID001Q3000006FpmoIACACCOUNTID"
    $s3 = "COMPANYID001Q3000008IyacIACACCOUNTID"
    $s4 = "COMPANYID001Q3000009QoSEIA0ACCOUNTID"
    $s5 = "COMPANYID001Q30000023c7iIAAACCOUNTID"
    $s6 = "COMPANYID001Q3000008qXbDIAUACCOUNTID"
    $s7 = "COMPANYID001Q3000008cfLjIAIACCOUNTID"
    $s8 = "COMPANYID001Q3000007hJubIAEACCOUNTID"
    $s9 = "COMPANYID001Q3000008ryO3IAIACCOUNTID"
    $s10 = "COMPANYID001Q300000A5nnAIARACCOUNTID"
    $s11 = "COMPANYID001Q3000008JfioIACACCOUNTID"
    $s12 = "COMPANYID001Q300000BeUp3IAFACCOUNTID"
    $s13 = "COMPANYID001Q3000005gMamIAEACCOUNTID"
    $s14 = "COMPANYID001Q3000005gMamIAEACCOUNTID"
    $s15 = "mrrobertcornish@gmail.comINTEGRATORLOGINCOMPANYID"

    $sc1 = { 0A 28 49 99 78 E5 89 8D F4 0A 23 8E B8 A5 52 E8 } // Atera Network certificate 2024-02-15 - 2025-03-18
    $sc2 = { 06 7F 60 47 95 66 24 A7 15 99 61 74 3D 81 94 93 } // Atera Network certificate 2022-02-17 - 2024-03-16

  condition:
    filesize > 1MB and filesize < 4MB
    and (uint16be(0) == 0xD0CF)
    and any of ($s*)
    and any of ($sc*)
}

rule muddywater_muddyc2go_launcher {
    meta:
        description = "Detects MuddyC2Go DLL launcher"
        author = "Sekoia.io"
        creation_date = "2024-03-07"
        hash = "1a0827082d4b517b643c86ee678eaa53f85f1b33ad409a23c50164c3909fdaca"
        
    strings:
        $ = "-Method GET -ErrorAction Stop;Write-Output $response.Content;iex $response.Content;"
        $ = "GetCurrentProcess"
        $ = "TerminateProcess"
        
    condition:
        uint16be(0) == 0x4d5a and
        filesize < 50KB and 
        all of them
}

rule muddywater_rotrot_strings {
    meta:
        description = "Detects RotRot backdoor based on strings"
        author = "Sekoia.io"
        creation_date = "2024-06-10"
        
    strings:
        $s1 = "qsphsbnebub"
        $s2 = "rtqitcofcvc"
        $s3 = "surjudpgdwd"
        $s4 = "tvskveqhexe"
        $s5 = "uwtlwfrifyf"
        $s6 = "vxumxgsjgzg"
        
        $t1 = "MpbeMjcsbs"
        $t2 = "NqcfNkdtct"
        $t3 = "OrdgOleudu"
        $t4 = "PsehPmfvev"
        $t5 = "QtfiQngwfw"
        $t6 = "RugjRohxgx"
        
        $u1 = "UfsnjobufKpcPckfdu"
        $u2 = "VgtokpcvgLqdQdlgev"
        $u3 = "WhuplqdwhMreRemhfw"
        $u4 = "XivqmrexiNsfSfnigx"
        $u5 = "YjwrnsfyjOtgTgojhy"
        $u6 = "ZkxsotgzkPuhUhpkiz"
        
    condition:
        uint16be(0) == 0x4d5a and
        filesize > 100KB and filesize < 300KB and
        any of ($s*) and any of ($t*) and any of ($u*)
}
        

rule coruna_exploit_mapjoinencoder {
	meta:
		author = "Google Threat Intelligence Group (GTIG)"
	strings:
		$s1 = /\[[^\]]+\]\.map\(\w\s*=>.{0,15}String\.fromCharCode\(\w\s*\^\s*(\d+)\).{0,15}\.join\(""\)/
		$fp1 = "bot|googlebot|crawler|spider|robot|crawling"
	condition:
		1 of ($s*) and not any of ($fp*)
}

rule coruna_backdoor_plasmagrid {
	meta:
		author = "Google Threat Intelligence Group (GTIG)"
	strings:
		$ = "com.plasma.appruntime.appdiscovery"
		$ = "com.plasma.appruntime.downloadmanager"
		$ = "com.plasma.appruntime.hotupdatemanager"
		$ = "com.plasma.appruntime.modulestore"
		$ = "com.plasma.appruntime.netconfig"
		$ = "com.plasma.bundlemapper"
		$ = "com.plasma.event.upload.serial"
		$ = "com.plasma.notes.monitor"
		$ = "com.plasma.photomonitor"
		$ = "com.plasma.PLProcessStateDetector"
		$ = "plasma_heartbeat_monitor"
		$ = "plasma_injection_dispatcher"
		$ = "plasma_ipc_processor"
		$ = "plasma_%@.jpg"
		$ = "/var/mobile/Library/Preferences/com.plasma.photomonitor.plist"
		$ = "helion_ipc_handler"
		$ = "PLInjectionStateInfo"
		$ = "PLExploitationInterface"
	condition:
		1 of them
}