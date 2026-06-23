// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Icons - Fluent UI icon enum 图标枚举
// Auto-generated from SVG folder, do not edit manually! 自动生成，请勿手动编辑！
// Total icons: 2484 图标总数
// Usage: Enums.icon.chevron_up 使用方式
pragma Singleton

QtObject {
    id: root
    
    readonly property string basePath: "fluent/"
    
    // Get icon path 获取图标路径
    function path(iconName) {
        return basePath + iconName + ".svg"
    }
    
    // Icon list for iteration 图标列表（用于遍历）
    readonly property var iconList: {
        "ACCESSIBILITY": "Accessibility",
        "ACCESSIBILITY_CHECKMARK": "AccessibilityCheckmark",
        "ACCESSIBILITY_ERROR": "AccessibilityError",
        "ACCESSIBILITY_MORE": "AccessibilityMore",
        "ACCESSIBILITY_QUESTION_MARK": "AccessibilityQuestionMark",
        "ACCESS_TIME": "AccessTime",
        "ADD": "Add",
        "ADD_CIRCLE": "AddCircle",
        "ADD_SQUARE": "AddSquare",
        "ADD_SQUARE_MULTIPLE": "AddSquareMultiple",
        "ADD_STARBURST": "AddStarburst",
        "ADD_SUBTRACT_CIRCLE": "AddSubtractCircle",
        "AGENTS": "Agents",
        "AGENTS_ADD": "AgentsAdd",
        "AIRPLANE": "Airplane",
        "AIRPLANE_LANDING": "AirplaneLanding",
        "AIRPLANE_TAKE_OFF": "AirplaneTakeOff",
        "ALBUM": "Album",
        "ALBUM_ADD": "AlbumAdd",
        "ALERT": "Alert",
        "ALERT_BADGE": "AlertBadge",
        "ALERT_OFF": "AlertOff",
        "ALERT_ON": "AlertOn",
        "ALERT_SNOOZE": "AlertSnooze",
        "ALERT_URGENT": "AlertUrgent",
        "ANIMAL_CAT": "AnimalCat",
        "ANIMAL_DOG": "AnimalDog",
        "ANIMAL_PAW_PRINT": "AnimalPawPrint",
        "ANIMAL_RABBIT": "AnimalRabbit",
        "ANIMAL_RABBIT_OFF": "AnimalRabbitOff",
        "ANIMAL_TURTLE": "AnimalTurtle",
        "APP_FOLDER": "AppFolder",
        "APP_GENERIC": "AppGeneric",
        "APP_RECENT": "AppRecent",
        "APPROVALS_APP": "ApprovalsApp",
        "APPS": "Apps",
        "APPS_ADD_IN": "AppsAddIn",
        "APPS_ADD_IN_OFF": "AppsAddInOff",
        "APPS_LIST": "AppsList",
        "APPS_LIST_DETAIL": "AppsListDetail",
        "APPS_SETTINGS": "AppsSettings",
        "APPS_SHIELD": "AppsShield",
        "APP_STORE": "AppStore",
        "APP_TITLE": "AppTitle",
        "ARCHIVE": "Archive",
        "ARCHIVE_ARROW_BACK": "ArchiveArrowBack",
        "ARCHIVE_CLOCK": "ArchiveClock",
        "ARCHIVE_MULTIPLE": "ArchiveMultiple",
        "ARCHIVE_SETTINGS": "ArchiveSettings",
        "ARROW_AUTOFIT_CONTENT": "ArrowAutofitContent",
        "ARROW_AUTOFIT_DOWN": "ArrowAutofitDown",
        "ARROW_AUTOFIT_HEIGHT": "ArrowAutofitHeight",
        "ARROW_AUTOFIT_HEIGHT_DOTTED": "ArrowAutofitHeightDotted",
        "ARROW_AUTOFIT_HEIGHT_IN": "ArrowAutofitHeightIn",
        "ARROW_AUTOFIT_UP": "ArrowAutofitUp",
        "ARROW_AUTOFIT_WIDTH": "ArrowAutofitWidth",
        "ARROW_AUTOFIT_WIDTH_DOTTED": "ArrowAutofitWidthDotted",
        "ARROW_BETWEEN_DOWN": "ArrowBetweenDown",
        "ARROW_BETWEEN_UP": "ArrowBetweenUp",
        "ARROW_BIDIRECTIONAL_LEFT_RIGHT": "ArrowBidirectionalLeftRight",
        "ARROW_BIDIRECTIONAL_UP_DOWN": "ArrowBidirectionalUpDown",
        "ARROW_BOUNCE": "ArrowBounce",
        "ARROW_CIRCLE_DOWN": "ArrowCircleDown",
        "ARROW_CIRCLE_DOWN_DOUBLE": "ArrowCircleDownDouble",
        "ARROW_CIRCLE_DOWN_RIGHT": "ArrowCircleDownRight",
        "ARROW_CIRCLE_DOWN_SPLIT": "ArrowCircleDownSplit",
        "ARROW_CIRCLE_DOWN_UP": "ArrowCircleDownUp",
        "ARROW_CIRCLE_LEFT": "ArrowCircleLeft",
        "ARROW_CIRCLE_RIGHT": "ArrowCircleRight",
        "ARROW_CIRCLE_UP": "ArrowCircleUp",
        "ARROW_CIRCLE_UP_LEFT": "ArrowCircleUpLeft",
        "ARROW_CIRCLE_UP_RIGHT": "ArrowCircleUpRight",
        "ARROW_CIRCLE_UP_SPARKLE": "ArrowCircleUpSparkle",
        "ARROW_CLOCKWISE": "ArrowClockwise",
        "ARROW_CLOCKWISE_DASHES": "ArrowClockwiseDashes",
        "ARROW_CLOCKWISE_DASHES_SETTINGS": "ArrowClockwiseDashesSettings",
        "ARROW_COLLAPSE_ALL": "ArrowCollapseAll",
        "ARROW_COUNTERCLOCKWISE": "ArrowCounterclockwise",
        "ARROW_COUNTERCLOCKWISE_DASHES": "ArrowCounterclockwiseDashes",
        "ARROW_COUNTERCLOCKWISE_INFO": "ArrowCounterclockwiseInfo",
        "ARROW_CURVE_DOWN_LEFT": "ArrowCurveDownLeft",
        "ARROW_CURVE_DOWN_RIGHT": "ArrowCurveDownRight",
        "ARROW_CURVE_UP_LEFT": "ArrowCurveUpLeft",
        "ARROW_CURVE_UP_RIGHT": "ArrowCurveUpRight",
        "ARROW_DOWN": "ArrowDown",
        "ARROW_DOWN_EXCLAMATION": "ArrowDownExclamation",
        "ARROW_DOWN_LEFT": "ArrowDownLeft",
        "ARROW_DOWNLOAD": "ArrowDownload",
        "ARROW_DOWNLOAD_OFF": "ArrowDownloadOff",
        "ARROW_DOWN_RIGHT": "ArrowDownRight",
        "ARROW_EJECT": "ArrowEject",
        "ARROW_ENTER": "ArrowEnter",
        "ARROW_ENTER_LEFT": "ArrowEnterLeft",
        "ARROW_ENTER_UP": "ArrowEnterUp",
        "ARROW_EXIT": "ArrowExit",
        "ARROW_EXPAND": "ArrowExpand",
        "ARROW_EXPAND_ALL": "ArrowExpandAll",
        "ARROW_EXPORT": "ArrowExport",
        "ARROW_EXPORT_L_T_R": "ArrowExportLTR",
        "ARROW_EXPORT_R_T_L": "ArrowExportRTL",
        "ARROW_EXPORT_UP": "ArrowExportUp",
        "ARROW_FIT": "ArrowFit",
        "ARROW_FIT_IN": "ArrowFitIn",
        "ARROW_FLOW_DIAGONAL_UP_RIGHT": "ArrowFlowDiagonalUpRight",
        "ARROW_FLOW_UP_RIGHT": "ArrowFlowUpRight",
        "ARROW_FLOW_UP_RIGHT_RECTANGLE_MULTIPLE": "ArrowFlowUpRightRectangleMultiple",
        "ARROW_FORWARD": "ArrowForward",
        "ARROW_FORWARD_DOWN_LIGHTNING": "ArrowForwardDownLightning",
        "ARROW_FORWARD_DOWN_PERSON": "ArrowForwardDownPerson",
        "ARROW_HOOK_DOWN_LEFT": "ArrowHookDownLeft",
        "ARROW_HOOK_DOWN_RIGHT": "ArrowHookDownRight",
        "ARROW_HOOK_UP_LEFT": "ArrowHookUpLeft",
        "ARROW_HOOK_UP_RIGHT": "ArrowHookUpRight",
        "ARROW_IMPORT": "ArrowImport",
        "ARROW_JOIN": "ArrowJoin",
        "ARROW_LEFT": "ArrowLeft",
        "ARROW_MAXIMIZE": "ArrowMaximize",
        "ARROW_MAXIMIZE_TOP_LEFT_BOTTOM_RIGHT": "ArrowMaximizeTopLeftBottomRight",
        "ARROW_MAXIMIZE_VERTICAL": "ArrowMaximizeVertical",
        "ARROW_MINIMIZE": "ArrowMinimize",
        "ARROW_MINIMIZE_TOP_LEFT_BOTTOM_RIGHT": "ArrowMinimizeTopLeftBottomRight",
        "ARROW_MINIMIZE_VERTICAL": "ArrowMinimizeVertical",
        "ARROW_MOVE": "ArrowMove",
        "ARROW_MOVE_INWARD": "ArrowMoveInward",
        "ARROW_NEXT": "ArrowNext",
        "ARROW_OUTLINE_DOWN_LEFT": "ArrowOutlineDownLeft",
        "ARROW_OUTLINE_UP_RIGHT": "ArrowOutlineUpRight",
        "ARROW_PARAGRAPH": "ArrowParagraph",
        "ARROW_PREVIOUS": "ArrowPrevious",
        "ARROW_REDO": "ArrowRedo",
        "ARROW_REDO_TEMP_L_T_R": "ArrowRedoTempLTR",
        "ARROW_REDO_TEMP_R_T_L": "ArrowRedoTempRTL",
        "ARROW_REPEAT1": "ArrowRepeat1",
        "ARROW_REPEAT_ALL": "ArrowRepeatAll",
        "ARROW_REPEAT_ALL_OFF": "ArrowRepeatAllOff",
        "ARROW_REPLY": "ArrowReply",
        "ARROW_REPLY_ALL": "ArrowReplyAll",
        "ARROW_REPLY_DOWN": "ArrowReplyDown",
        "ARROW_RESET": "ArrowReset",
        "ARROW_RIGHT": "ArrowRight",
        "ARROW_ROTATE_CLOCKWISE": "ArrowRotateClockwise",
        "ARROW_ROTATE_COUNTERCLOCKWISE": "ArrowRotateCounterclockwise",
        "ARROW_ROUTING": "ArrowRouting",
        "ARROW_ROUTING_RECTANGLE_MULTIPLE": "ArrowRoutingRectangleMultiple",
        "ARROWS_BIDIRECTIONAL": "ArrowsBidirectional",
        "ARROW_SHUFFLE": "ArrowShuffle",
        "ARROW_SHUFFLE_OFF": "ArrowShuffleOff",
        "ARROW_SORT": "ArrowSort",
        "ARROW_SORT_DOWN": "ArrowSortDown",
        "ARROW_SORT_DOWN_LINES": "ArrowSortDownLines",
        "ARROW_SORT_UP": "ArrowSortUp",
        "ARROW_SORT_UP_LINES": "ArrowSortUpLines",
        "ARROW_SPLIT": "ArrowSplit",
        "ARROW_SPRINT": "ArrowSprint",
        "ARROW_SQUARE_DOWN": "ArrowSquareDown",
        "ARROW_SQUARE_UP_RIGHT": "ArrowSquareUpRight",
        "ARROW_STEP_BACK": "ArrowStepBack",
        "ARROW_STEP_IN": "ArrowStepIn",
        "ARROW_STEP_IN_DIAGONAL_DOWN_LEFT": "ArrowStepInDiagonalDownLeft",
        "ARROW_STEP_IN_LEFT": "ArrowStepInLeft",
        "ARROW_STEP_IN_RIGHT": "ArrowStepInRight",
        "ARROW_STEP_OUT": "ArrowStepOut",
        "ARROW_STEP_OVER": "ArrowStepOver",
        "ARROW_SWAP": "ArrowSwap",
        "ARROW_SYNC": "ArrowSync",
        "ARROW_SYNC_CHECKMARK": "ArrowSyncCheckmark",
        "ARROW_SYNC_CIRCLE": "ArrowSyncCircle",
        "ARROW_SYNC_DISMISS": "ArrowSyncDismiss",
        "ARROW_SYNC_OFF": "ArrowSyncOff",
        "ARROW_TRENDING": "ArrowTrending",
        "ARROW_TRENDING_CHECKMARK": "ArrowTrendingCheckmark",
        "ARROW_TRENDING_DOWN": "ArrowTrendingDown",
        "ARROW_TRENDING_LINES": "ArrowTrendingLines",
        "ARROW_TRENDING_SETTINGS": "ArrowTrendingSettings",
        "ARROW_TRENDING_SPARKLE": "ArrowTrendingSparkle",
        "ARROW_TRENDING_TEXT": "ArrowTrendingText",
        "ARROW_TRENDING_WRENCH": "ArrowTrendingWrench",
        "ARROW_TURN_BIDIRECTIONAL_DOWN_RIGHT": "ArrowTurnBidirectionalDownRight",
        "ARROW_TURN_DOWN_LEFT": "ArrowTurnDownLeft",
        "ARROW_TURN_DOWN_RIGHT": "ArrowTurnDownRight",
        "ARROW_TURN_DOWN_UP": "ArrowTurnDownUp",
        "ARROW_TURN_LEFT_DOWN": "ArrowTurnLeftDown",
        "ARROW_TURN_LEFT_RIGHT": "ArrowTurnLeftRight",
        "ARROW_TURN_LEFT_UP": "ArrowTurnLeftUp",
        "ARROW_TURN_RIGHT": "ArrowTurnRight",
        "ARROW_TURN_RIGHT_DOWN": "ArrowTurnRightDown",
        "ARROW_TURN_RIGHT_LEFT": "ArrowTurnRightLeft",
        "ARROW_TURN_RIGHT_UP": "ArrowTurnRightUp",
        "ARROW_TURN_UP_DOWN": "ArrowTurnUpDown",
        "ARROW_TURN_UP_LEFT": "ArrowTurnUpLeft",
        "ARROW_UNDO": "ArrowUndo",
        "ARROW_UNDO_TEMP_L_T_R": "ArrowUndoTempLTR",
        "ARROW_UNDO_TEMP_R_T_L": "ArrowUndoTempRTL",
        "ARROW_UP": "ArrowUp",
        "ARROW_UP_EXCLAMATION": "ArrowUpExclamation",
        "ARROW_UP_LEFT": "ArrowUpLeft",
        "ARROW_UPLOAD": "ArrowUpload",
        "ARROW_UP_RIGHT": "ArrowUpRight",
        "ARROW_UP_RIGHT_DASHES": "ArrowUpRightDashes",
        "ARROW_UP_SQUARE_SETTINGS": "ArrowUpSquareSettings",
        "ARROW_WRAP": "ArrowWrap",
        "ARROW_WRAP_OFF": "ArrowWrapOff",
        "ARROW_WRAP_UP_TO_DOWN": "ArrowWrapUpToDown",
        "ATTACH": "Attach",
        "ATTACH_ARROW_RIGHT": "AttachArrowRight",
        "ATTACH_TEXT": "AttachText",
        "AUTOCORRECT": "Autocorrect",
        "AUTO_FIT_HEIGHT": "AutoFitHeight",
        "AUTO_FIT_WIDTH": "AutoFitWidth",
        "AUTO_SUM": "AutoSum",
        "BACKPACK": "Backpack",
        "BACKPACK_ADD": "BackpackAdd",
        "BACKSPACE": "Backspace",
        "BADGE": "Badge",
        "BALCONY": "Balcony",
        "BALLOON": "Balloon",
        "BARCODE_SCANNER": "BarcodeScanner",
        "BARCODE_SCANNER_ADD": "BarcodeScannerAdd",
        "BARCODE_SCANNER_DISMISS": "BarcodeScannerDismiss",
        "BATTERY0": "Battery0",
        "BATTERY1": "Battery1",
        "BATTERY10": "Battery10",
        "BATTERY2": "Battery2",
        "BATTERY3": "Battery3",
        "BATTERY4": "Battery4",
        "BATTERY5": "Battery5",
        "BATTERY6": "Battery6",
        "BATTERY7": "Battery7",
        "BATTERY8": "Battery8",
        "BATTERY9": "Battery9",
        "BATTERY_CHARGE": "BatteryCharge",
        "BATTERY_CHARGE0": "BatteryCharge0",
        "BATTERY_CHARGE1": "BatteryCharge1",
        "BATTERY_CHARGE10": "BatteryCharge10",
        "BATTERY_CHARGE2": "BatteryCharge2",
        "BATTERY_CHARGE3": "BatteryCharge3",
        "BATTERY_CHARGE4": "BatteryCharge4",
        "BATTERY_CHARGE5": "BatteryCharge5",
        "BATTERY_CHARGE6": "BatteryCharge6",
        "BATTERY_CHARGE7": "BatteryCharge7",
        "BATTERY_CHARGE8": "BatteryCharge8",
        "BATTERY_CHARGE9": "BatteryCharge9",
        "BATTERY_CHECKMARK": "BatteryCheckmark",
        "BATTERY_SAVER": "BatterySaver",
        "BATTERY_WARNING": "BatteryWarning",
        "BEACH": "Beach",
        "BEAKER": "Beaker",
        "BEAKER_ADD": "BeakerAdd",
        "BEAKER_DISMISS": "BeakerDismiss",
        "BEAKER_EDIT": "BeakerEdit",
        "BEAKER_EMPTY": "BeakerEmpty",
        "BEAKER_OFF": "BeakerOff",
        "BEAKER_SETTINGS": "BeakerSettings",
        "BED": "Bed",
        "BENCH": "Bench",
        "BEZIER_CURVE_SQUARE": "BezierCurveSquare",
        "BINDER_TRIANGLE": "BinderTriangle",
        "BIN_FULL": "BinFull",
        "BIN_RECYCLE": "BinRecycle",
        "BIN_RECYCLE_FULL": "BinRecycleFull",
        "BLUETOOTH": "Bluetooth",
        "BLUETOOTH_CONNECTED": "BluetoothConnected",
        "BLUETOOTH_DISABLED": "BluetoothDisabled",
        "BLUETOOTH_SEARCHING": "BluetoothSearching",
        "BLUR": "Blur",
        "BOARD": "Board",
        "BOARD_GAMES": "BoardGames",
        "BOARD_HEART": "BoardHeart",
        "BOARD_SPLIT": "BoardSplit",
        "BOOK": "Book",
        "BOOK_ADD": "BookAdd",
        "BOOK_ARROW_CLOCKWISE": "BookArrowClockwise",
        "BOOK_CLOCK": "BookClock",
        "BOOK_COINS": "BookCoins",
        "BOOK_COMPASS": "BookCompass",
        "BOOK_CONTACTS": "BookContacts",
        "BOOK_DATABASE": "BookDatabase",
        "BOOK_DISMISS": "BookDismiss",
        "BOOK_EXCLAMATION_MARK": "BookExclamationMark",
        "BOOK_GLOBE": "BookGlobe",
        "BOOK_INFORMATION": "BookInformation",
        "BOOK_LETTER": "BookLetter",
        "BOOKMARK": "Bookmark",
        "BOOKMARK_ADD": "BookmarkAdd",
        "BOOKMARK_MULTIPLE": "BookmarkMultiple",
        "BOOKMARK_OFF": "BookmarkOff",
        "BOOKMARK_SEARCH": "BookmarkSearch",
        "BOOK_NUMBER": "BookNumber",
        "BOOK_OPEN": "BookOpen",
        "BOOK_OPEN_GLOBE": "BookOpenGlobe",
        "BOOK_OPEN_LIGHTBULB": "BookOpenLightbulb",
        "BOOK_OPEN_MICROPHONE": "BookOpenMicrophone",
        "BOOK_PULSE": "BookPulse",
        "BOOK_QUESTION_MARK": "BookQuestionMark",
        "BOOK_QUESTION_MARK_R_T_L": "BookQuestionMarkRTL",
        "BOOK_SEARCH": "BookSearch",
        "BOOK_STAR": "BookStar",
        "BOOK_TEMPLATE": "BookTemplate",
        "BOOK_THETA": "BookTheta",
        "BOOK_TOOLBOX": "BookToolbox",
        "BOT": "Bot",
        "BOT_ADD": "BotAdd",
        "BOT_SPARKLE": "BotSparkle",
        "BOWL_CHOPSTICKS": "BowlChopsticks",
        "BOWL_SALAD": "BowlSalad",
        "BOW_TIE": "BowTie",
        "BOX": "Box",
        "BOX_ARROW_LEFT": "BoxArrowLeft",
        "BOX_ARROW_UP": "BoxArrowUp",
        "BOX_CHECKMARK": "BoxCheckmark",
        "BOX_DISMISS": "BoxDismiss",
        "BOX_EDIT": "BoxEdit",
        "BOX_MULTIPLE": "BoxMultiple",
        "BOX_MULTIPLE_ARROW_LEFT": "BoxMultipleArrowLeft",
        "BOX_MULTIPLE_ARROW_RIGHT": "BoxMultipleArrowRight",
        "BOX_MULTIPLE_CHECKMARK": "BoxMultipleCheckmark",
        "BOX_MULTIPLE_SEARCH": "BoxMultipleSearch",
        "BOX_SEARCH": "BoxSearch",
        "BOX_TOOLBOX": "BoxToolbox",
        "BRACES": "Braces",
        "BRACES_CHECKMARK": "BracesCheckmark",
        "BRACES_DISMISS": "BracesDismiss",
        "BRACES_VARIABLE": "BracesVariable",
        "BRAIN": "Brain",
        "BRAIN_CIRCUIT": "BrainCircuit",
        "BRAIN_SPARKLE": "BrainSparkle",
        "BRANCH": "Branch",
        "BRANCH_COMPARE": "BranchCompare",
        "BRANCH_FORK": "BranchFork",
        "BRANCH_FORK_HINT": "BranchForkHint",
        "BRANCH_FORK_LINK": "BranchForkLink",
        "BRANCH_REQUEST": "BranchRequest",
        "BRANCH_REQUEST_CLOSED": "BranchRequestClosed",
        "BRANCH_REQUEST_DRAFT": "BranchRequestDraft",
        "BREAKOUT_ROOM": "BreakoutRoom",
        "BRIEFCASE": "Briefcase",
        "BRIEFCASE_MEDICAL": "BriefcaseMedical",
        "BRIEFCASE_OFF": "BriefcaseOff",
        "BRIEFCASE_PERSON": "BriefcasePerson",
        "BRIEFCASE_SEARCH": "BriefcaseSearch",
        "BRIGHTNESS_HIGH": "BrightnessHigh",
        "BRIGHTNESS_LOW": "BrightnessLow",
        "BROAD_ACTIVITY_FEED": "BroadActivityFeed",
        "BROOM": "Broom",
        "BROOM_SPARKLE": "BroomSparkle",
        "BUBBLE_MULTIPLE": "BubbleMultiple",
        "BUG": "Bug",
        "BUG_ARROW_COUNTERCLOCKWISE": "BugArrowCounterclockwise",
        "BUG_PROHIBITED": "BugProhibited",
        "BUILDING": "Building",
        "BUILDING_BANK": "BuildingBank",
        "BUILDING_BANK_LINK": "BuildingBankLink",
        "BUILDING_BANK_TOOLBOX": "BuildingBankToolbox",
        "BUILDING_CHECKMARK": "BuildingCheckmark",
        "BUILDING_CLOUD": "BuildingCloud",
        "BUILDING_DESKTOP": "BuildingDesktop",
        "BUILDING_FACTORY": "BuildingFactory",
        "BUILDING_GOVERNMENT": "BuildingGovernment",
        "BUILDING_GOVERNMENT_SEARCH": "BuildingGovernmentSearch",
        "BUILDING_HOME": "BuildingHome",
        "BUILDING_LIGHTHOUSE": "BuildingLighthouse",
        "BUILDING_MOSQUE": "BuildingMosque",
        "BUILDING_MULTIPLE": "BuildingMultiple",
        "BUILDING_PEOPLE": "BuildingPeople",
        "BUILDING_RETAIL": "BuildingRetail",
        "BUILDING_RETAIL_MONEY": "BuildingRetailMoney",
        "BUILDING_RETAIL_MORE": "BuildingRetailMore",
        "BUILDING_RETAIL_SHIELD": "BuildingRetailShield",
        "BUILDING_RETAIL_TOOLBOX": "BuildingRetailToolbox",
        "BUILDING_SHOP": "BuildingShop",
        "BUILDING_SKYSCRAPER": "BuildingSkyscraper",
        "BUILDING_SWAP": "BuildingSwap",
        "BUILDING_TOWNHOUSE": "BuildingTownhouse",
        "BUILDING_YURT": "BuildingYurt",
        "BUTTON": "Button",
        "CALCULATOR": "Calculator",
        "CALCULATOR_ARROW_CLOCKWISE": "CalculatorArrowClockwise",
        "CALCULATOR_MULTIPLE": "CalculatorMultiple",
        "CALENDAR": "Calendar",
        "CALL": "Call",
        "CALL_ADD": "CallAdd",
        "CALL_CHECKMARK": "CallCheckmark",
        "CALL_CONNECTING": "CallConnecting",
        "CALL_DISMISS": "CallDismiss",
        "CALL_END": "CallEnd",
        "CALL_EXCLAMATION": "CallExclamation",
        "CALL_FORWARD": "CallForward",
        "CALLIGRAPHY_PEN": "CalligraphyPen",
        "CALLIGRAPHY_PEN_CHECKMARK": "CalligraphyPenCheckmark",
        "CALLIGRAPHY_PEN_ERROR": "CalligraphyPenError",
        "CALLIGRAPHY_PEN_QUESTION_MARK": "CalligraphyPenQuestionMark",
        "CALL_INBOUND": "CallInbound",
        "CALL_MISSED": "CallMissed",
        "CALL_OUTBOUND": "CallOutbound",
        "CALL_PARK": "CallPark",
        "CALL_PAUSE": "CallPause",
        "CALL_PROHIBITED": "CallProhibited",
        "CALL_RECTANGLE_LANDSCAPE": "CallRectangleLandscape",
        "CALL_SQUARE": "CallSquare",
        "CALL_TRANSFER": "CallTransfer",
        "CALL_WARNING": "CallWarning",
        "CAMERA": "Camera",
        "CAMERA_ADD": "CameraAdd",
        "CAMERA_ARROW_UP": "CameraArrowUp",
        "CAMERA_DOME": "CameraDome",
        "CAMERA_EDIT": "CameraEdit",
        "CAMERA_OFF": "CameraOff",
        "CAMERA_SPARKLES": "CameraSparkles",
        "CAMERA_SWITCH": "CameraSwitch",
        "CARD_U_I": "CardUI",
        "CARD_U_I_PORTRAIT_FLIP": "CardUIPortraitFlip",
        "CARET_DOWN": "CaretDown",
        "CARET_DOWN_RIGHT": "CaretDownRight",
        "CARET_LEFT": "CaretLeft",
        "CARET_RIGHT": "CaretRight",
        "CARET_UP": "CaretUp",
        "CART": "Cart",
        "CAST": "Cast",
        "CAST_MULTIPLE": "CastMultiple",
        "CATCH_UP": "CatchUp",
        "C_D": "CD",
        "CELLULAR3_G": "Cellular3G",
        "CELLULAR4_G": "Cellular4G",
        "CELLULAR5_G": "Cellular5G",
        "CELLULAR_DATA1": "CellularData1",
        "CELLULAR_DATA2": "CellularData2",
        "CELLULAR_DATA3": "CellularData3",
        "CELLULAR_DATA4": "CellularData4",
        "CELLULAR_DATA5": "CellularData5",
        "CELLULAR_OFF": "CellularOff",
        "CELLULAR_WARNING": "CellularWarning",
        "CENTER_HORIZONTAL": "CenterHorizontal",
        "CENTER_VERTICAL": "CenterVertical",
        "CERTIFICATE": "Certificate",
        "CHANNEL": "Channel",
        "CHANNEL_ADD": "ChannelAdd",
        "CHANNEL_ALERT": "ChannelAlert",
        "CHANNEL_ARROW_LEFT": "ChannelArrowLeft",
        "CHANNEL_DISMISS": "ChannelDismiss",
        "CHANNEL_SHARE": "ChannelShare",
        "CHANNEL_SUBTRACT": "ChannelSubtract",
        "CHART_MULTIPLE": "ChartMultiple",
        "CHART_PERSON": "ChartPerson",
        "CHAT": "Chat",
        "CHAT_ADD": "ChatAdd",
        "CHAT_ARROW_BACK": "ChatArrowBack",
        "CHAT_ARROW_BACK_DOWN": "ChatArrowBackDown",
        "CHAT_ARROW_DOUBLE_BACK": "ChatArrowDoubleBack",
        "CHAT_BUBBLES_QUESTION": "ChatBubblesQuestion",
        "CHAT_CURSOR": "ChatCursor",
        "CHAT_DISMISS": "ChatDismiss",
        "CHAT_EMPTY": "ChatEmpty",
        "CHAT_HELP": "ChatHelp",
        "CHAT_HINT_HALF": "ChatHintHalf",
        "CHAT_HISTORY": "ChatHistory",
        "CHAT_LOCK": "ChatLock",
        "CHAT_MAIL": "ChatMail",
        "CHAT_MULTIPLE": "ChatMultiple",
        "CHAT_MULTIPLE_CHECKMARK": "ChatMultipleCheckmark",
        "CHAT_MULTIPLE_HEART": "ChatMultipleHeart",
        "CHAT_MULTIPLE_MINUS": "ChatMultipleMinus",
        "CHAT_OFF": "ChatOff",
        "CHAT_SETTINGS": "ChatSettings",
        "CHAT_SPARKLE": "ChatSparkle",
        "CHAT_VIDEO": "ChatVideo",
        "CHAT_WARNING": "ChatWarning",
        "CHECK": "Check",
        "CHECKBOX1": "Checkbox1",
        "CHECKBOX2": "Checkbox2",
        "CHECKBOX_ARROW_RIGHT": "CheckboxArrowRight",
        "CHECKBOX_CHECKED": "CheckboxChecked",
        "CHECKBOX_CHECKED_SYNC": "CheckboxCheckedSync",
        "CHECKBOX_INDETERMINATE": "CheckboxIndeterminate",
        "CHECKBOX_PERSON": "CheckboxPerson",
        "CHECKBOX_UNCHECKED": "CheckboxUnchecked",
        "CHECKBOX_WARNING": "CheckboxWarning",
        "CHECKMARK": "Checkmark",
        "CHECKMARK_CIRCLE": "CheckmarkCircle",
        "CHECKMARK_CIRCLE_HINT": "CheckmarkCircleHint",
        "CHECKMARK_CIRCLE_SQUARE": "CheckmarkCircleSquare",
        "CHECKMARK_CIRCLE_WARNING": "CheckmarkCircleWarning",
        "CHECKMARK_LOCK": "CheckmarkLock",
        "CHECKMARK_NOTE": "CheckmarkNote",
        "CHECKMARK_SQUARE": "CheckmarkSquare",
        "CHECKMARK_STARBURST": "CheckmarkStarburst",
        "CHECKMARK_UNDERLINE_CIRCLE": "CheckmarkUnderlineCircle",
        "CHESS": "Chess",
        "CHEVRON_CIRCLE_DOWN": "ChevronCircleDown",
        "CHEVRON_CIRCLE_LEFT": "ChevronCircleLeft",
        "CHEVRON_CIRCLE_RIGHT": "ChevronCircleRight",
        "CHEVRON_CIRCLE_UP": "ChevronCircleUp",
        "CHEVRON_DOUBLE_DOWN": "ChevronDoubleDown",
        "CHEVRON_DOUBLE_LEFT": "ChevronDoubleLeft",
        "CHEVRON_DOUBLE_RIGHT": "ChevronDoubleRight",
        "CHEVRON_DOUBLE_UP": "ChevronDoubleUp",
        "CHEVRON_DOWN": "ChevronDown",
        "CHEVRON_DOWN_UP": "ChevronDownUp",
        "CHEVRON_LEFT": "ChevronLeft",
        "CHEVRON_RIGHT": "ChevronRight",
        "CHEVRON_UP": "ChevronUp",
        "CHEVRON_UP_DOWN": "ChevronUpDown",
        "CIRCLE": "Circle",
        "CIRCLE_EDIT": "CircleEdit",
        "CIRCLE_ERASER": "CircleEraser",
        "CIRCLE_HALF_FILL": "CircleHalfFill",
        "CIRCLE_HIGHLIGHT": "CircleHighlight",
        "CIRCLE_HINT": "CircleHint",
        "CIRCLE_HINT_CURSOR": "CircleHintCursor",
        "CIRCLE_HINT_DISMISS": "CircleHintDismiss",
        "CIRCLE_HINT_HALF_VERTICAL": "CircleHintHalfVertical",
        "CIRCLE_IMAGE": "CircleImage",
        "CIRCLE_LINE": "CircleLine",
        "CIRCLE_MULTIPLE_CONCENTRIC": "CircleMultipleConcentric",
        "CIRCLE_MULTIPLE_HINT_CHECKMARK": "CircleMultipleHintCheckmark",
        "CIRCLE_MULTIPLE_SUBTRACT_CHECKMARK": "CircleMultipleSubtractCheckmark",
        "CIRCLE_OFF": "CircleOff",
        "CIRCLE_SHADOW": "CircleShadow",
        "CIRCLE_SMALL": "CircleSmall",
        "CIRCLE_SPARKLE": "CircleSparkle",
        "CITY": "City",
        "CLASS": "Class",
        "CLASSIFICATION": "Classification",
        "CLEAR_FORMATTING": "ClearFormatting",
        "CLIPBOARD": "Clipboard",
        "CLOCK": "Clock",
        "CLOCK_ALARM": "ClockAlarm",
        "CLOCK_ARROW_DOWNLOAD": "ClockArrowDownload",
        "CLOCK_BILL": "ClockBill",
        "CLOCK_DISMISS": "ClockDismiss",
        "CLOCK_LOCK": "ClockLock",
        "CLOCK_PAUSE": "ClockPause",
        "CLOCK_SPARKLE": "ClockSparkle",
        "CLOCK_TOOLBOX": "ClockToolbox",
        "CLOCK_WARNING": "ClockWarning",
        "CLOSED_CAPTION": "ClosedCaption",
        "CLOSED_CAPTION_OFF": "ClosedCaptionOff",
        "CLOTHES_HANGER": "ClothesHanger",
        "CLOUD": "Cloud",
        "CLOUD_ADD": "CloudAdd",
        "CLOUD_ARCHIVE": "CloudArchive",
        "CLOUD_ARROW_DOWN": "CloudArrowDown",
        "CLOUD_ARROW_RIGHT": "CloudArrowRight",
        "CLOUD_ARROW_UP": "CloudArrowUp",
        "CLOUD_BEAKER": "CloudBeaker",
        "CLOUD_BIDIRECTIONAL": "CloudBidirectional",
        "CLOUD_CHECKMARK": "CloudCheckmark",
        "CLOUD_CUBE": "CloudCube",
        "CLOUD_DATABASE": "CloudDatabase",
        "CLOUD_DESKTOP": "CloudDesktop",
        "CLOUD_DISMISS": "CloudDismiss",
        "CLOUD_EDIT": "CloudEdit",
        "CLOUD_ERROR": "CloudError",
        "CLOUD_FLOW": "CloudFlow",
        "CLOUD_LINK": "CloudLink",
        "CLOUD_OFF": "CloudOff",
        "CLOUD_SWAP": "CloudSwap",
        "CLOUD_SYNC": "CloudSync",
        "CLOUD_WORDS": "CloudWords",
        "CLOVER": "Clover",
        "CODE": "Code",
        "CODE_BLOCK": "CodeBlock",
        "CODE_BLOCK_EDIT": "CodeBlockEdit",
        "CODE_CIRCLE": "CodeCircle",
        "CODE_C_S": "CodeCS",
        "CODE_C_S_RECTANGLE": "CodeCSRectangle",
        "CODE_F_S": "CodeFS",
        "CODE_F_S_RECTANGLE": "CodeFSRectangle",
        "CODE_J_S": "CodeJS",
        "CODE_J_S_RECTANGLE": "CodeJSRectangle",
        "CODE_P_Y": "CodePY",
        "CODE_P_Y_RECTANGLE": "CodePYRectangle",
        "CODE_R_B": "CodeRB",
        "CODE_R_B_RECTANGLE": "CodeRBRectangle",
        "CODE_TEXT": "CodeText",
        "CODE_TEXT_EDIT": "CodeTextEdit",
        "CODE_TEXT_OFF": "CodeTextOff",
        "CODE_T_S": "CodeTS",
        "CODE_T_S_RECTANGLE": "CodeTSRectangle",
        "CODE_V_B": "CodeVB",
        "CODE_V_B_RECTANGLE": "CodeVBRectangle",
        "COIN_MULTIPLE": "CoinMultiple",
        "COIN_STACK": "CoinStack",
        "COLLECTIONS": "Collections",
        "COLLECTIONS_ADD": "CollectionsAdd",
        "COLLECTIONS_EMPTY": "CollectionsEmpty",
        "COLOR": "Color",
        "COLOR_BACKGROUND": "ColorBackground",
        "COLOR_BACKGROUND_ACCENT": "ColorBackgroundAccent",
        "COLOR_FILL": "ColorFill",
        "COLOR_FILL_ACCENT": "ColorFillAccent",
        "COLOR_LINE": "ColorLine",
        "COLOR_LINE_ACCENT": "ColorLineAccent",
        "COLUMN": "Column",
        "COLUMN_ARROW_RIGHT": "ColumnArrowRight",
        "COLUMN_DOUBLE_COMPARE": "ColumnDoubleCompare",
        "COLUMN_EDIT": "ColumnEdit",
        "COLUMN_SINGLE": "ColumnSingle",
        "COLUMN_SINGLE_COMPARE": "ColumnSingleCompare",
        "COLUMN_TRIPLE": "ColumnTriple",
        "COLUMN_TRIPLE_EDIT": "ColumnTripleEdit",
        "COMMA": "Comma",
        "COMMENT": "Comment",
        "COMMENT_ADD": "CommentAdd",
        "COMMENT_ARROW_LEFT": "CommentArrowLeft",
        "COMMENT_ARROW_LEFT_TEMP_L_T_R": "CommentArrowLeftTempLTR",
        "COMMENT_ARROW_LEFT_TEMP_R_T_L": "CommentArrowLeftTempRTL",
        "COMMENT_ARROW_RIGHT": "CommentArrowRight",
        "COMMENT_ARROW_RIGHT_TEMP_L_T_R": "CommentArrowRightTempLTR",
        "COMMENT_ARROW_RIGHT_TEMP_R_T_L": "CommentArrowRightTempRTL",
        "COMMENT_BADGE": "CommentBadge",
        "COMMENT_CHECKMARK": "CommentCheckmark",
        "COMMENT_DISMISS": "CommentDismiss",
        "COMMENT_EDIT": "CommentEdit",
        "COMMENT_ERROR": "CommentError",
        "COMMENT_LIGHTNING": "CommentLightning",
        "COMMENT_LINK": "CommentLink",
        "COMMENT_MENTION": "CommentMention",
        "COMMENT_MULTIPLE": "CommentMultiple",
        "COMMENT_MULTIPLE_CHECKMARK": "CommentMultipleCheckmark",
        "COMMENT_MULTIPLE_LINK": "CommentMultipleLink",
        "COMMENT_MULTIPLE_MENTION": "CommentMultipleMention",
        "COMMENT_NOTE": "CommentNote",
        "COMMENT_OFF": "CommentOff",
        "COMMENT_QUOTE": "CommentQuote",
        "COMMENT_TEXT": "CommentText",
        "COMMUNICATION": "Communication",
        "COMMUNICATION_PERSON": "CommunicationPerson",
        "COMMUNICATION_SHIELD": "CommunicationShield",
        "COMPASS_NORTHWEST": "CompassNorthwest",
        "COMPASS_TRUE_NORTH": "CompassTrueNorth",
        "COMPONENT2_DOUBLE_TAP_SWIPE_DOWN": "Component2DoubleTapSwipeDown",
        "COMPONENT2_DOUBLE_TAP_SWIPE_UP": "Component2DoubleTapSwipeUp",
        "COMPOSE": "Compose",
        "CONE": "Cone",
        "CONFERENCE_ROOM": "ConferenceRoom",
        "CONNECTED": "Connected",
        "CONNECTOR": "Connector",
        "CONTACT_CARD": "ContactCard",
        "CONTACT_CARD_GENERIC": "ContactCardGeneric",
        "CONTACT_CARD_GROUP": "ContactCardGroup",
        "CONTACT_CARD_LINK": "ContactCardLink",
        "CONTACT_CARD_RIBBON": "ContactCardRibbon",
        "CONTENT_SETTINGS": "ContentSettings",
        "CONTENT_VIEW": "ContentView",
        "CONTENT_VIEW_GALLERY": "ContentViewGallery",
        "CONTENT_VIEW_GALLERY_LIGHTNING": "ContentViewGalleryLightning",
        "CONTRACT_DOWN_LEFT": "ContractDownLeft",
        "CONTRACT_UP_RIGHT": "ContractUpRight",
        "CONTROL_BUTTON": "ControlButton",
        "CONVERT_RANGE": "ConvertRange",
        "COOKIES": "Cookies",
        "COPY": "Copy",
        "COPY_ADD": "CopyAdd",
        "COPY_ARROW_RIGHT": "CopyArrowRight",
        "COPY_SELECT": "CopySelect",
        "COUCH": "Couch",
        "COUNTER": "Counter",
        "CREDIT_CARD_CLOCK": "CreditCardClock",
        "CREDIT_CARD_PERSON": "CreditCardPerson",
        "CREDIT_CARD_TOOLBOX": "CreditCardToolbox",
        "CROP": "Crop",
        "CROP_ARROW_ROTATE": "CropArrowRotate",
        "CROP_INTERIM": "CropInterim",
        "CROP_INTERIM_OFF": "CropInterimOff",
        "CROP_SPARKLE": "CropSparkle",
        "CROWN": "Crown",
        "CROWN_SUBTRACT": "CrownSubtract",
        "CUBE": "Cube",
        "CUBE_ADD": "CubeAdd",
        "CUBE_ARROW_CURVE_DOWN": "CubeArrowCurveDown",
        "CUBE_CHECKMARK": "CubeCheckmark",
        "CUBE_LINK": "CubeLink",
        "CUBE_MULTIPLE": "CubeMultiple",
        "CUBE_QUICK": "CubeQuick",
        "CUBE_ROTATE": "CubeRotate",
        "CUBE_SYNC": "CubeSync",
        "CUBE_TREE": "CubeTree",
        "CURRENCY_DOLLAR_EURO": "CurrencyDollarEuro",
        "CURRENCY_DOLLAR_RUPEE": "CurrencyDollarRupee",
        "CURSOR": "Cursor",
        "CURSOR_CLICK": "CursorClick",
        "CURSOR_HOVER": "CursorHover",
        "CURSOR_HOVER_OFF": "CursorHoverOff",
        "CURSOR_PROHIBITED": "CursorProhibited",
        "CUT": "Cut",
        "DARK_THEME": "DarkTheme",
        "DATA_AREA": "DataArea",
        "DATA_BAR_HORIZONTAL": "DataBarHorizontal",
        "DATA_BAR_HORIZONTAL_DESCENDING": "DataBarHorizontalDescending",
        "DATA_BAR_VERTICAL": "DataBarVertical",
        "DATA_BAR_VERTICAL_ADD": "DataBarVerticalAdd",
        "DATA_BAR_VERTICAL_ARROW_DOWN": "DataBarVerticalArrowDown",
        "DATA_BAR_VERTICAL_ASCENDING": "DataBarVerticalAscending",
        "DATA_BAR_VERTICAL_EDIT": "DataBarVerticalEdit",
        "DATA_BAR_VERTICAL_STAR": "DataBarVerticalStar",
        "DATABASE": "Database",
        "DATABASE_ARROW_DOWN": "DatabaseArrowDown",
        "DATABASE_ARROW_RIGHT": "DatabaseArrowRight",
        "DATABASE_ARROW_UP": "DatabaseArrowUp",
        "DATABASE_CHECKMARK": "DatabaseCheckmark",
        "DATABASE_LIGHTNING": "DatabaseLightning",
        "DATABASE_LINK": "DatabaseLink",
        "DATABASE_MULTIPLE": "DatabaseMultiple",
        "DATABASE_PERSON": "DatabasePerson",
        "DATABASE_PLUG_CONNECTED": "DatabasePlugConnected",
        "DATABASE_SEARCH": "DatabaseSearch",
        "DATABASE_STACK": "DatabaseStack",
        "DATABASE_SWITCH": "DatabaseSwitch",
        "DATABASE_WARNING": "DatabaseWarning",
        "DATABASE_WINDOW": "DatabaseWindow",
        "DATA_FUNNEL": "DataFunnel",
        "DATA_HISTOGRAM": "DataHistogram",
        "DATA_LINE": "DataLine",
        "DATA_PIE": "DataPie",
        "DATA_SCATTER": "DataScatter",
        "DATA_SUNBURST": "DataSunburst",
        "DATA_TREEMAP": "DataTreemap",
        "DATA_TRENDING": "DataTrending",
        "DATA_USAGE": "DataUsage",
        "DATA_USAGE_CHECKMARK": "DataUsageCheckmark",
        "DATA_USAGE_EDIT": "DataUsageEdit",
        "DATA_USAGE_SETTINGS": "DataUsageSettings",
        "DATA_USAGE_SPARKLE": "DataUsageSparkle",
        "DATA_USAGE_TOOLBOX": "DataUsageToolbox",
        "DATA_WATERFALL": "DataWaterfall",
        "DATA_WHISKER": "DataWhisker",
        "DECIMAL_ARROW_LEFT": "DecimalArrowLeft",
        "DECIMAL_ARROW_RIGHT": "DecimalArrowRight",
        "DELETE": "Delete",
        "DELETE_ARROW_BACK": "DeleteArrowBack",
        "DELETE_DISMISS": "DeleteDismiss",
        "DELETE_LINES": "DeleteLines",
        "DELETE_OFF": "DeleteOff",
        "DENTIST": "Dentist",
        "DESIGN_IDEAS": "DesignIdeas",
        "DESK": "Desk",
        "DESK_MULTIPLE": "DeskMultiple",
        "DESK_SPARKLE": "DeskSparkle",
        "DESKTOP": "Desktop",
        "DESKTOP_ARROW_DOWN": "DesktopArrowDown",
        "DESKTOP_ARROW_DOWN_OFF": "DesktopArrowDownOff",
        "DESKTOP_ARROW_RIGHT": "DesktopArrowRight",
        "DESKTOP_CHECKMARK": "DesktopCheckmark",
        "DESKTOP_CURSOR": "DesktopCursor",
        "DESKTOP_EDIT": "DesktopEdit",
        "DESKTOP_FLOW": "DesktopFlow",
        "DESKTOP_KEYBOARD": "DesktopKeyboard",
        "DESKTOP_MAC": "DesktopMac",
        "DESKTOP_OFF": "DesktopOff",
        "DESKTOP_PULSE": "DesktopPulse",
        "DESKTOP_SIGNAL": "DesktopSignal",
        "DESKTOP_SPEAKER": "DesktopSpeaker",
        "DESKTOP_SPEAKER_OFF": "DesktopSpeakerOff",
        "DESKTOP_SYNC": "DesktopSync",
        "DESKTOP_TOOLBOX": "DesktopToolbox",
        "DESKTOP_TOWER": "DesktopTower",
        "DEVELOPER_BOARD": "DeveloperBoard",
        "DEVELOPER_BOARD_LIGHTNING": "DeveloperBoardLightning",
        "DEVELOPER_BOARD_LIGHTNING_TOOLBOX": "DeveloperBoardLightningToolbox",
        "DEVELOPER_BOARD_SEARCH": "DeveloperBoardSearch",
        "DEVICE_E_Q": "DeviceEQ",
        "DEVICE_MEETING_ROOM": "DeviceMeetingRoom",
        "DEVICE_MEETING_ROOM_ALL_IN_ONE": "DeviceMeetingRoomAllInOne",
        "DEVICE_MEETING_ROOM_BAR": "DeviceMeetingRoomBar",
        "DEVICE_MEETING_ROOM_REMOTE": "DeviceMeetingRoomRemote",
        "DIAGRAM": "Diagram",
        "DIALPAD": "Dialpad",
        "DIALPAD_OFF": "DialpadOff",
        "DIALPAD_QUESTION_MARK": "DialpadQuestionMark",
        "DIAMOND": "Diamond",
        "DIAMOND_DISMISS": "DiamondDismiss",
        "DIAMOND_LINK": "DiamondLink",
        "DIRECTIONS": "Directions",
        "DISHWASHER": "Dishwasher",
        "DISMISS": "Dismiss",
        "DISMISS_CIRCLE": "DismissCircle",
        "DISMISS_SQUARE": "DismissSquare",
        "DISMISS_SQUARE_MULTIPLE": "DismissSquareMultiple",
        "DIVERSITY": "Diversity",
        "DIVIDER_SHORT": "DividerShort",
        "DIVIDER_TALL": "DividerTall",
        "DOCK": "Dock",
        "DOCK_ROW": "DockRow",
        "DOCTOR": "Doctor",
        "DOCUMENT": "Document",
        "DOCUMENT100": "Document100",
        "DOCUMENT_ADD": "DocumentAdd",
        "DOCUMENT_ARROW_DOWN": "DocumentArrowDown",
        "DOCUMENT_ARROW_LEFT": "DocumentArrowLeft",
        "DOCUMENT_ARROW_RIGHT": "DocumentArrowRight",
        "DOCUMENT_ARROW_UP": "DocumentArrowUp",
        "DOCUMENT_BORDER_PRINT": "DocumentBorderPrint",
        "DOCUMENT_BRIEFCASE": "DocumentBriefcase",
        "DOCUMENT_BULLET_LIST": "DocumentBulletList",
        "DOCUMENT_BULLET_LIST_ARROW_LEFT": "DocumentBulletListArrowLeft",
        "DOCUMENT_BULLET_LIST_CLOCK": "DocumentBulletListClock",
        "DOCUMENT_BULLET_LIST_CUBE": "DocumentBulletListCube",
        "DOCUMENT_BULLET_LIST_MULTIPLE": "DocumentBulletListMultiple",
        "DOCUMENT_BULLET_LIST_OFF": "DocumentBulletListOff",
        "DOCUMENT_CATCH_UP": "DocumentCatchUp",
        "DOCUMENT_CHECKMARK": "DocumentCheckmark",
        "DOCUMENT_CHEVRON_DOUBLE": "DocumentChevronDouble",
        "DOCUMENT_CODE": "DocumentCode",
        "DOCUMENT_CONTRACT": "DocumentContract",
        "DOCUMENT_COPY": "DocumentCopy",
        "DOCUMENT_C_S": "DocumentCS",
        "DOCUMENT_C_S_S": "DocumentCSS",
        "DOCUMENT_C_S_V": "DocumentCSV",
        "DOCUMENT_CUBE": "DocumentCube",
        "DOCUMENT_DATA": "DocumentData",
        "DOCUMENT_DATABASE": "DocumentDatabase",
        "DOCUMENT_DATA_LINK": "DocumentDataLink",
        "DOCUMENT_DATA_LOCK": "DocumentDataLock",
        "DOCUMENT_DISMISS": "DocumentDismiss",
        "DOCUMENT_EDIT": "DocumentEdit",
        "DOCUMENT_ENDNOTE": "DocumentEndnote",
        "DOCUMENT_ERROR": "DocumentError",
        "DOCUMENT_FIT": "DocumentFit",
        "DOCUMENT_FLOWCHART": "DocumentFlowchart",
        "DOCUMENT_FOLDER": "DocumentFolder",
        "DOCUMENT_FOOTER": "DocumentFooter",
        "DOCUMENT_FOOTER_DISMISS": "DocumentFooterDismiss",
        "DOCUMENT_F_S": "DocumentFS",
        "DOCUMENT_GLOBE": "DocumentGlobe",
        "DOCUMENT_HEADER": "DocumentHeader",
        "DOCUMENT_HEADER_ARROW_DOWN": "DocumentHeaderArrowDown",
        "DOCUMENT_HEADER_DISMISS": "DocumentHeaderDismiss",
        "DOCUMENT_HEADER_FOOTER": "DocumentHeaderFooter",
        "DOCUMENT_HEART": "DocumentHeart",
        "DOCUMENT_HEART_PULSE": "DocumentHeartPulse",
        "DOCUMENT_IMAGE": "DocumentImage",
        "DOCUMENT_J_A_V_A": "DocumentJAVA",
        "DOCUMENT_JAVASCRIPT": "DocumentJavascript",
        "DOCUMENT_J_S": "DocumentJS",
        "DOCUMENT_KEY": "DocumentKey",
        "DOCUMENT_LANDSCAPE": "DocumentLandscape",
        "DOCUMENT_LANDSCAPE_DATA": "DocumentLandscapeData",
        "DOCUMENT_LANDSCAPE_SPLIT": "DocumentLandscapeSplit",
        "DOCUMENT_LANDSCAPE_SPLIT_HINT": "DocumentLandscapeSplitHint",
        "DOCUMENT_LIGHTNING": "DocumentLightning",
        "DOCUMENT_LINK": "DocumentLink",
        "DOCUMENT_LOCK": "DocumentLock",
        "DOCUMENT_MARGINS": "DocumentMargins",
        "DOCUMENT_MENTION": "DocumentMention",
        "DOCUMENT_MULTIPLE": "DocumentMultiple",
        "DOCUMENT_MULTIPLE_PERCENT": "DocumentMultiplePercent",
        "DOCUMENT_MULTIPLE_PROHIBITED": "DocumentMultipleProhibited",
        "DOCUMENT_MULTIPLE_SYNC": "DocumentMultipleSync",
        "DOCUMENT_NUMBER1": "DocumentNumber1",
        "DOCUMENT_ONE_PAGE": "DocumentOnePage",
        "DOCUMENT_ONE_PAGE_ADD": "DocumentOnePageAdd",
        "DOCUMENT_ONE_PAGE_BEAKER": "DocumentOnePageBeaker",
        "DOCUMENT_ONE_PAGE_COLUMNS": "DocumentOnePageColumns",
        "DOCUMENT_ONE_PAGE_LINK": "DocumentOnePageLink",
        "DOCUMENT_ONE_PAGE_MULTIPLE": "DocumentOnePageMultiple",
        "DOCUMENT_ONE_PAGE_MULTIPLE_SPARKLE": "DocumentOnePageMultipleSparkle",
        "DOCUMENT_ONE_PAGE_SPARKLE": "DocumentOnePageSparkle",
        "DOCUMENT_PAGE_BOTTOM_CENTER": "DocumentPageBottomCenter",
        "DOCUMENT_PAGE_BOTTOM_LEFT": "DocumentPageBottomLeft",
        "DOCUMENT_PAGE_BOTTOM_RIGHT": "DocumentPageBottomRight",
        "DOCUMENT_PAGE_BREAK": "DocumentPageBreak",
        "DOCUMENT_PAGE_NUMBER": "DocumentPageNumber",
        "DOCUMENT_PAGE_TOP_CENTER": "DocumentPageTopCenter",
        "DOCUMENT_PAGE_TOP_LEFT": "DocumentPageTopLeft",
        "DOCUMENT_PAGE_TOP_RIGHT": "DocumentPageTopRight",
        "DOCUMENT_P_D_F": "DocumentPDF",
        "DOCUMENT_PERCENT": "DocumentPercent",
        "DOCUMENT_PERSON": "DocumentPerson",
        "DOCUMENT_PILL": "DocumentPill",
        "DOCUMENT_PRINT": "DocumentPrint",
        "DOCUMENT_PROHIBITED": "DocumentProhibited",
        "DOCUMENT_P_Y": "DocumentPY",
        "DOCUMENT_QUESTION_MARK": "DocumentQuestionMark",
        "DOCUMENT_QUEUE": "DocumentQueue",
        "DOCUMENT_QUEUE_ADD": "DocumentQueueAdd",
        "DOCUMENT_QUEUE_MULTIPLE": "DocumentQueueMultiple",
        "DOCUMENT_R_B": "DocumentRB",
        "DOCUMENT_RIBBON": "DocumentRibbon",
        "DOCUMENT_S_A_S_S": "DocumentSASS",
        "DOCUMENT_SAVE": "DocumentSave",
        "DOCUMENT_SEARCH": "DocumentSearch",
        "DOCUMENT_SETTINGS": "DocumentSettings",
        "DOCUMENT_SIGNATURE": "DocumentSignature",
        "DOCUMENT_SPARKLE": "DocumentSparkle",
        "DOCUMENT_SPLIT_HINT": "DocumentSplitHint",
        "DOCUMENT_SPLIT_HINT_OFF": "DocumentSplitHintOff",
        "DOCUMENT_SQUARE": "DocumentSquare",
        "DOCUMENT_SYNC": "DocumentSync",
        "DOCUMENT_TABLE": "DocumentTable",
        "DOCUMENT_TABLE_ARROW_RIGHT": "DocumentTableArrowRight",
        "DOCUMENT_TABLE_CHECKMARK": "DocumentTableCheckmark",
        "DOCUMENT_TABLE_CUBE": "DocumentTableCube",
        "DOCUMENT_TABLE_SEARCH": "DocumentTableSearch",
        "DOCUMENT_TABLE_TRUCK": "DocumentTableTruck",
        "DOCUMENT_TARGET": "DocumentTarget",
        "DOCUMENT_TEXT": "DocumentText",
        "DOCUMENT_TEXT_CLOCK": "DocumentTextClock",
        "DOCUMENT_TEXT_EXTRACT": "DocumentTextExtract",
        "DOCUMENT_TEXT_LINK": "DocumentTextLink",
        "DOCUMENT_TEXT_TOOLBOX": "DocumentTextToolbox",
        "DOCUMENT_TOOLBOX": "DocumentToolbox",
        "DOCUMENT_T_S": "DocumentTS",
        "DOCUMENT_V_B": "DocumentVB",
        "DOCUMENT_WIDTH": "DocumentWidth",
        "DOCUMENT_Y_M_L": "DocumentYML",
        "DOOR": "Door",
        "DOOR_ARROW_LEFT": "DoorArrowLeft",
        "DOOR_ARROW_RIGHT": "DoorArrowRight",
        "DOOR_TAG": "DoorTag",
        "DOUBLE_SWIPE_DOWN": "DoubleSwipeDown",
        "DOUBLE_SWIPE_UP": "DoubleSwipeUp",
        "DOUBLE_TAP_SWIPE_DOWN": "DoubleTapSwipeDown",
        "DOUBLE_TAP_SWIPE_UP": "DoubleTapSwipeUp",
        "DRAFTS": "Drafts",
        "DRAG": "Drag",
        "DRAWER": "Drawer",
        "DRAWER_ADD": "DrawerAdd",
        "DRAWER_ARROW_DOWNLOAD": "DrawerArrowDownload",
        "DRAWER_DISMISS": "DrawerDismiss",
        "DRAWER_PLAY": "DrawerPlay",
        "DRAWER_SUBTRACT": "DrawerSubtract",
        "DRAW_IMAGE": "DrawImage",
        "DRAW_SHAPE": "DrawShape",
        "DRAW_TEXT": "DrawText",
        "DRINK_BEER": "DrinkBeer",
        "DRINK_BOTTLE": "DrinkBottle",
        "DRINK_BOTTLE_OFF": "DrinkBottleOff",
        "DRINK_COFFEE": "DrinkCoffee",
        "DRINK_MARGARITA": "DrinkMargarita",
        "DRINK_TO_GO": "DrinkToGo",
        "DRINK_WINE": "DrinkWine",
        "DRIVE_TRAIN": "DriveTrain",
        "DROP": "Drop",
        "DUAL_SCREEN": "DualScreen",
        "DUAL_SCREEN_ADD": "DualScreenAdd",
        "DUAL_SCREEN_ARROW_RIGHT": "DualScreenArrowRight",
        "DUAL_SCREEN_ARROW_UP": "DualScreenArrowUp",
        "DUAL_SCREEN_CLOCK": "DualScreenClock",
        "DUAL_SCREEN_CLOSED_ALERT": "DualScreenClosedAlert",
        "DUAL_SCREEN_DESKTOP": "DualScreenDesktop",
        "DUAL_SCREEN_DISMISS": "DualScreenDismiss",
        "DUAL_SCREEN_GROUP": "DualScreenGroup",
        "DUAL_SCREEN_HEADER": "DualScreenHeader",
        "DUAL_SCREEN_LOCK": "DualScreenLock",
        "DUAL_SCREEN_MIRROR": "DualScreenMirror",
        "DUAL_SCREEN_PAGINATION": "DualScreenPagination",
        "DUAL_SCREEN_SETTINGS": "DualScreenSettings",
        "DUAL_SCREEN_SPAN": "DualScreenSpan",
        "DUAL_SCREEN_SPEAKER": "DualScreenSpeaker",
        "DUAL_SCREEN_STATUS_BAR": "DualScreenStatusBar",
        "DUAL_SCREEN_TABLET": "DualScreenTablet",
        "DUAL_SCREEN_UPDATE": "DualScreenUpdate",
        "DUAL_SCREEN_VERTICAL_SCROLL": "DualScreenVerticalScroll",
        "DUAL_SCREEN_VIBRATE": "DualScreenVibrate",
        "DUMBBELL": "Dumbbell",
        "DUST": "Dust",
        "EARTH": "Earth",
        "EARTH_LEAF": "EarthLeaf",
        "EDIT": "Edit",
        "EDIT_ARROW_BACK": "EditArrowBack",
        "EDIT_LINE_HORIZONTAL3": "EditLineHorizontal3",
        "EDIT_LOCK": "EditLock",
        "EDIT_OFF": "EditOff",
        "EDIT_PERSON": "EditPerson",
        "EDIT_PROHIBITED": "EditProhibited",
        "EDIT_SETTINGS": "EditSettings",
        "ELEVATOR": "Elevator",
        "EMOJI": "Emoji",
        "EMOJI_ADD": "EmojiAdd",
        "EMOJI_ANGRY": "EmojiAngry",
        "EMOJI_EDIT": "EmojiEdit",
        "EMOJI_HAND": "EmojiHand",
        "EMOJI_HINT": "EmojiHint",
        "EMOJI_LAUGH": "EmojiLaugh",
        "EMOJI_MEH": "EmojiMeh",
        "EMOJI_MEME": "EmojiMeme",
        "EMOJI_MULTIPLE": "EmojiMultiple",
        "EMOJI_SAD": "EmojiSad",
        "EMOJI_SAD_SLIGHT": "EmojiSadSlight",
        "EMOJI_SMILE_SLIGHT": "EmojiSmileSlight",
        "EMOJI_SPARKLE": "EmojiSparkle",
        "EMOJI_SURPRISE": "EmojiSurprise",
        "ENGINE": "Engine",
        "EQUAL_CIRCLE": "EqualCircle",
        "EQUAL_OFF": "EqualOff",
        "ERASER": "Eraser",
        "ERASER_MEDIUM": "EraserMedium",
        "ERASER_SEGMENT": "EraserSegment",
        "ERASER_SMALL": "EraserSmall",
        "ERASER_TOOL": "EraserTool",
        "ERROR_CIRCLE": "ErrorCircle",
        "ERROR_CIRCLE_SETTINGS": "ErrorCircleSettings",
        "EXPAND_UP_LEFT": "ExpandUpLeft",
        "EXPAND_UP_RIGHT": "ExpandUpRight",
        "EXTENDED_DOCK": "ExtendedDock",
        "EYE": "Eye",
        "EYE_CIRCLE": "EyeCircle",
        "EYEDROPPER": "Eyedropper",
        "EYEDROPPER_OFF": "EyedropperOff",
        "EYE_LINES": "EyeLines",
        "EYE_OFF": "EyeOff",
        "EYE_TRACKING": "EyeTracking",
        "EYE_TRACKING_OFF": "EyeTrackingOff",
        "FAST_ACCELERATION": "FastAcceleration",
        "FAST_FORWARD": "FastForward",
        "FAX": "Fax",
        "FEED": "Feed",
        "FILMSTRIP": "Filmstrip",
        "FILMSTRIP_IMAGE": "FilmstripImage",
        "FILMSTRIP_PLAY": "FilmstripPlay",
        "FILMSTRIP_SPLIT": "FilmstripSplit",
        "FILTER": "Filter",
        "FILTER_ADD": "FilterAdd",
        "FILTER_DISMISS": "FilterDismiss",
        "FILTER_SYNC": "FilterSync",
        "FINGERPRINT": "Fingerprint",
        "FIRE": "Fire",
        "FIREPLACE": "Fireplace",
        "FIXED_WIDTH": "FixedWidth",
        "FLAG": "Flag",
        "FLAG_CHECKERED": "FlagCheckered",
        "FLAG_CLOCK": "FlagClock",
        "FLAG_OFF": "FlagOff",
        "FLASH": "Flash",
        "FLASH_ADD": "FlashAdd",
        "FLASH_AUTO": "FlashAuto",
        "FLASH_CHECKMARK": "FlashCheckmark",
        "FLASH_FLOW": "FlashFlow",
        "FLASHLIGHT": "Flashlight",
        "FLASHLIGHT_OFF": "FlashlightOff",
        "FLASH_OFF": "FlashOff",
        "FLASH_PLAY": "FlashPlay",
        "FLASH_SETTINGS": "FlashSettings",
        "FLASH_SPARKLE": "FlashSparkle",
        "FLIP_HORIZONTAL": "FlipHorizontal",
        "FLIP_VERTICAL": "FlipVertical",
        "FLOW": "Flow",
        "FLOWCHART": "Flowchart",
        "FLOWCHART_CIRCLE": "FlowchartCircle",
        "FLOW_DOT": "FlowDot",
        "FLOW_SPARKLE": "FlowSparkle",
        "FLUENT": "Fluent",
        "FLUID": "Fluid",
        "FOLDER": "Folder",
        "FOLDER_ADD": "FolderAdd",
        "FOLDER_ARROW_LEFT": "FolderArrowLeft",
        "FOLDER_ARROW_RIGHT": "FolderArrowRight",
        "FOLDER_ARROW_UP": "FolderArrowUp",
        "FOLDER_BRIEFCASE": "FolderBriefcase",
        "FOLDER_DOCUMENT": "FolderDocument",
        "FOLDER_GLOBE": "FolderGlobe",
        "FOLDER_LIGHTNING": "FolderLightning",
        "FOLDER_LINK": "FolderLink",
        "FOLDER_LIST": "FolderList",
        "FOLDER_MAIL": "FolderMail",
        "FOLDER_MULTIPLE": "FolderMultiple",
        "FOLDER_OPEN": "FolderOpen",
        "FOLDER_OPEN_DOWN": "FolderOpenDown",
        "FOLDER_OPEN_VERTICAL": "FolderOpenVertical",
        "FOLDER_PEOPLE": "FolderPeople",
        "FOLDER_PERSON": "FolderPerson",
        "FOLDER_PROHIBITED": "FolderProhibited",
        "FOLDER_SEARCH": "FolderSearch",
        "FOLDER_SWAP": "FolderSwap",
        "FOLDER_SYNC": "FolderSync",
        "FOLDER_ZIP": "FolderZip",
        "FONT_DECREASE": "FontDecrease",
        "FONT_INCREASE": "FontIncrease",
        "FONT_SPACE_TRACKING_IN": "FontSpaceTrackingIn",
        "FONT_SPACE_TRACKING_OUT": "FontSpaceTrackingOut",
        "FOOD": "Food",
        "FOOD_APPLE": "FoodApple",
        "FOOD_CAKE": "FoodCake",
        "FOOD_CARROT": "FoodCarrot",
        "FOOD_CHICKEN_LEG": "FoodChickenLeg",
        "FOOD_EGG": "FoodEgg",
        "FOOD_FISH": "FoodFish",
        "FOOD_GRAINS": "FoodGrains",
        "FOOD_PIZZA": "FoodPizza",
        "FOOD_TOAST": "FoodToast",
        "FORM": "Form",
        "FORM_MULTIPLE": "FormMultiple",
        "FORM_MULTIPLE_COLLECTION": "FormMultipleCollection",
        "FORM_NEW": "FormNew",
        "FORM_SPARKLE": "FormSparkle",
        "F_P_S120": "FPS120",
        "F_P_S240": "FPS240",
        "F_P_S30": "FPS30",
        "F_P_S60": "FPS60",
        "F_P_S960": "FPS960",
        "FRAME": "Frame",
        "F_STOP": "FStop",
        "FULL_SCREEN_MAXIMIZE": "FullScreenMaximize",
        "FULL_SCREEN_MINIMIZE": "FullScreenMinimize",
        "GAME_CHAT": "GameChat",
        "GAMES": "Games",
        "GANTT_CHART": "GanttChart",
        "GAS": "Gas",
        "GAS_PROPANE": "GasPropane",
        "GAS_PUMP": "GasPump",
        "GATHER": "Gather",
        "GAUGE": "Gauge",
        "GAUGE_ADD": "GaugeAdd",
        "GAVEL": "Gavel",
        "GAVEL_PROHIBITED": "GavelProhibited",
        "GESTURE": "Gesture",
        "G_I_F": "GIF",
        "GIFT": "Gift",
        "GIFT_CARD": "GiftCard",
        "GIFT_CARD_ADD": "GiftCardAdd",
        "GIFT_CARD_ARROW_RIGHT": "GiftCardArrowRight",
        "GIFT_CARD_MONEY": "GiftCardMoney",
        "GIFT_CARD_MULTIPLE": "GiftCardMultiple",
        "GIFT_OPEN": "GiftOpen",
        "GLANCE": "Glance",
        "GLANCE_HORIZONTAL": "GlanceHorizontal",
        "GLANCE_HORIZONTAL_SPARKLES": "GlanceHorizontalSparkles",
        "GLASSES": "Glasses",
        "GLASSES_OFF": "GlassesOff",
        "GLOBE": "Globe",
        "GLOBE_ADD": "GlobeAdd",
        "GLOBE_ARROW_FORWARD": "GlobeArrowForward",
        "GLOBE_ARROW_UP": "GlobeArrowUp",
        "GLOBE_CLOCK": "GlobeClock",
        "GLOBE_DESKTOP": "GlobeDesktop",
        "GLOBE_ERROR": "GlobeError",
        "GLOBE_LOCATION": "GlobeLocation",
        "GLOBE_OFF": "GlobeOff",
        "GLOBE_PERSON": "GlobePerson",
        "GLOBE_PROHIBITED": "GlobeProhibited",
        "GLOBE_SEARCH": "GlobeSearch",
        "GLOBE_SHIELD": "GlobeShield",
        "GLOBE_STAR": "GlobeStar",
        "GLOBE_SURFACE": "GlobeSurface",
        "GLOBE_SYNC": "GlobeSync",
        "GLOBE_VIDEO": "GlobeVideo",
        "GLOBE_WARNING": "GlobeWarning",
        "GRID": "Grid",
        "GRID_CIRCLES": "GridCircles",
        "GRID_DOTS": "GridDots",
        "GRID_KANBAN": "GridKanban",
        "GROUP": "Group",
        "GROUP_DISMISS": "GroupDismiss",
        "GROUP_LIST": "GroupList",
        "GROUP_RETURN": "GroupReturn",
        "GUARDIAN": "Guardian",
        "GUEST": "Guest",
        "GUEST_ADD": "GuestAdd",
        "GUITAR": "Guitar",
        "HAND_DRAW": "HandDraw",
        "HAND_LEFT": "HandLeft",
        "HAND_LEFT_CHAT": "HandLeftChat",
        "HAND_MULTIPLE": "HandMultiple",
        "HAND_OPEN_HEART": "HandOpenHeart",
        "HAND_POINT": "HandPoint",
        "HAND_RIGHT": "HandRight",
        "HAND_RIGHT_OFF": "HandRightOff",
        "HANDSHAKE": "Handshake",
        "HAND_WAVE": "HandWave",
        "HAPTIC_STRONG": "HapticStrong",
        "HAPTIC_WEAK": "HapticWeak",
        "HARD_DRIVE": "HardDrive",
        "HARD_DRIVE_CALL": "HardDriveCall",
        "HAT_GRADUATION": "HatGraduation",
        "HAT_GRADUATION_ADD": "HatGraduationAdd",
        "HAT_GRADUATION_SPARKLE": "HatGraduationSparkle",
        "H_D": "HD",
        "H_D_OFF": "HDOff",
        "H_D_R": "HDR",
        "H_D_R_OFF": "HDROff",
        "HEADPHONES": "Headphones",
        "HEADPHONES_SOUND_WAVE": "HeadphonesSoundWave",
        "HEADSET": "Headset",
        "HEADSET_ADD": "HeadsetAdd",
        "HEADSET_V_R": "HeadsetVR",
        "HEART": "Heart",
        "HEART_BROKEN": "HeartBroken",
        "HEART_CIRCLE": "HeartCircle",
        "HEART_CIRCLE_HINT": "HeartCircleHint",
        "HEART_OFF": "HeartOff",
        "HEART_PULSE": "HeartPulse",
        "HEART_PULSE_CHECKMARK": "HeartPulseCheckmark",
        "HEART_PULSE_ERROR": "HeartPulseError",
        "HEART_PULSE_WARNING": "HeartPulseWarning",
        "HEXAGON": "Hexagon",
        "HEXAGON_SPARKLE": "HexagonSparkle",
        "HEXAGON_THREE": "HexagonThree",
        "HIGHLIGHT": "Highlight",
        "HIGHLIGHT_LINK": "HighlightLink",
        "HIGHWAY": "Highway",
        "HISTORY": "History",
        "HISTORY_DISMISS": "HistoryDismiss",
        "HOME": "Home",
        "HOME_ADD": "HomeAdd",
        "HOME_CHECKMARK": "HomeCheckmark",
        "HOME_DATABASE": "HomeDatabase",
        "HOME_EMPTY": "HomeEmpty",
        "HOME_GARAGE": "HomeGarage",
        "HOME_HEART": "HomeHeart",
        "HOME_MORE": "HomeMore",
        "HOME_PERSON": "HomePerson",
        "HOME_SPLIT": "HomeSplit",
        "HOURGLASS": "Hourglass",
        "HOURGLASS_HALF": "HourglassHalf",
        "HOURGLASS_ONE_QUARTER": "HourglassOneQuarter",
        "HOURGLASS_THREE_QUARTER": "HourglassThreeQuarter",
        "ICONS": "Icons",
        "IMAGE": "Image",
        "IMAGE_ADD": "ImageAdd",
        "IMAGE_ALT_TEXT": "ImageAltText",
        "IMAGE_ARROW_BACK": "ImageArrowBack",
        "IMAGE_ARROW_COUNTERCLOCKWISE": "ImageArrowCounterclockwise",
        "IMAGE_ARROW_FORWARD": "ImageArrowForward",
        "IMAGE_BORDER": "ImageBorder",
        "IMAGE_CIRCLE": "ImageCircle",
        "IMAGE_COPY": "ImageCopy",
        "IMAGE_EDIT": "ImageEdit",
        "IMAGE_GLOBE": "ImageGlobe",
        "IMAGE_MULTIPLE": "ImageMultiple",
        "IMAGE_MULTIPLE_OFF": "ImageMultipleOff",
        "IMAGE_OFF": "ImageOff",
        "IMAGE_PROHIBITED": "ImageProhibited",
        "IMAGE_REFLECTION": "ImageReflection",
        "IMAGE_SEARCH": "ImageSearch",
        "IMAGE_SHADOW": "ImageShadow",
        "IMAGE_SPARKLE": "ImageSparkle",
        "IMAGE_SPLIT": "ImageSplit",
        "IMAGE_STACK": "ImageStack",
        "IMAGE_TABLE": "ImageTable",
        "IMMERSIVE_READER": "ImmersiveReader",
        "IMPORTANT": "Important",
        "INCOGNITO": "Incognito",
        "INFO": "Info",
        "INFO_SHIELD": "InfoShield",
        "INFO_SPARKLE": "InfoSparkle",
        "INKING_TOOL": "InkingTool",
        "INK_STROKE": "InkStroke",
        "INK_STROKE_ARROW_DOWN": "InkStrokeArrowDown",
        "INK_STROKE_ARROW_UP_DOWN": "InkStrokeArrowUpDown",
        "IN_PRIVATE_ACCOUNT": "InPrivateAccount",
        "INSERT": "Insert",
        "I_O_S_ARROW": "iOSArrow",
        "I_O_S_ARROW_L_T_R": "iOSArrowLTR",
        "I_O_S_ARROW_R_T_L": "iOSArrowRTL",
        "I_O_S_CHEVRON_RIGHT": "iOSChevronRight",
        "IO_T": "IoT",
        "IO_T_ALERT": "IoTAlert",
        "ITEM_COMPARE": "ItemCompare",
        "JAVA_SCRIPT": "JavaScript",
        "JOYSTICK": "Joystick",
        "KEY": "Key",
        "KEYBOARD": "Keyboard",
        "KEYBOARD123": "Keyboard123",
        "KEYBOARD_DOCK": "KeyboardDock",
        "KEYBOARD_LAYOUT_FLOAT": "KeyboardLayoutFloat",
        "KEYBOARD_LAYOUT_ONE_HANDED_LEFT": "KeyboardLayoutOneHandedLeft",
        "KEYBOARD_LAYOUT_RESIZE": "KeyboardLayoutResize",
        "KEYBOARD_LAYOUT_SPLIT": "KeyboardLayoutSplit",
        "KEYBOARD_MOUSE": "KeyboardMouse",
        "KEYBOARD_SHIFT": "KeyboardShift",
        "KEYBOARD_SHIFT_UPPERCASE": "KeyboardShiftUppercase",
        "KEYBOARD_TAB": "KeyboardTab",
        "KEY_COMMAND": "KeyCommand",
        "KEY_MULTIPLE": "KeyMultiple",
        "KEY_RESET": "KeyReset",
        "KIOSK": "Kiosk",
        "LAPTOP": "Laptop",
        "LAPTOP_BRIEFCASE": "LaptopBriefcase",
        "LAPTOP_DISMISS": "LaptopDismiss",
        "LAPTOP_MULTIPLE": "LaptopMultiple",
        "LAPTOP_PERSON": "LaptopPerson",
        "LAPTOP_SETTINGS": "LaptopSettings",
        "LAPTOP_SHIELD": "LaptopShield",
        "LASER_TOOL": "LaserTool",
        "LASSO": "Lasso",
        "LAUNCHER_SETTINGS": "LauncherSettings",
        "LAYER": "Layer",
        "LAYER_DIAGONAL": "LayerDiagonal",
        "LAYER_DIAGONAL_ADD": "LayerDiagonalAdd",
        "LAYER_DIAGONAL_PERSON": "LayerDiagonalPerson",
        "LAYER_DIAGONAL_SPARKLE": "LayerDiagonalSparkle",
        "LAYOUT_ADD_ABOVE": "LayoutAddAbove",
        "LAYOUT_ADD_BELOW": "LayoutAddBelow",
        "LAYOUT_CELL_FOUR": "LayoutCellFour",
        "LAYOUT_COLUMN_FOUR": "LayoutColumnFour",
        "LAYOUT_COLUMN_ONE_THIRD_LEFT": "LayoutColumnOneThirdLeft",
        "LAYOUT_COLUMN_ONE_THIRD_RIGHT": "LayoutColumnOneThirdRight",
        "LAYOUT_COLUMN_ONE_THIRD_RIGHT_HINT": "LayoutColumnOneThirdRightHint",
        "LAYOUT_COLUMN_THREE": "LayoutColumnThree",
        "LAYOUT_COLUMN_TWO": "LayoutColumnTwo",
        "LAYOUT_COLUMN_TWO_EDIT": "LayoutColumnTwoEdit",
        "LAYOUT_COLUMN_TWO_SPLIT_LEFT": "LayoutColumnTwoSplitLeft",
        "LAYOUT_COLUMN_TWO_SPLIT_RIGHT": "LayoutColumnTwoSplitRight",
        "LAYOUT_DYNAMIC": "LayoutDynamic",
        "LAYOUT_ROW_FOUR": "LayoutRowFour",
        "LAYOUT_ROW_THREE": "LayoutRowThree",
        "LAYOUT_ROW_TWO": "LayoutRowTwo",
        "LAYOUT_ROW_TWO_SETTINGS": "LayoutRowTwoSettings",
        "LAYOUT_ROW_TWO_SPLIT_BOTTOM": "LayoutRowTwoSplitBottom",
        "LAYOUT_ROW_TWO_SPLIT_TOP": "LayoutRowTwoSplitTop",
        "LEAF_ONE": "LeafOne",
        "LEAF_THREE": "LeafThree",
        "LEAF_TWO": "LeafTwo",
        "LEARNING_APP": "LearningApp",
        "LIBRARY": "Library",
        "LIGHTBULB": "Lightbulb",
        "LIGHTBULB_CHECKMARK": "LightbulbCheckmark",
        "LIGHTBULB_CIRCLE": "LightbulbCircle",
        "LIGHTBULB_FILAMENT": "LightbulbFilament",
        "LIGHTBULB_PERSON": "LightbulbPerson",
        "LIKERT": "Likert",
        "LINE": "Line",
        "LINE_DASHES": "LineDashes",
        "LINE_FLOW_DIAGONAL_UP_RIGHT": "LineFlowDiagonalUpRight",
        "LINE_HORIZONTAL1": "LineHorizontal1",
        "LINE_HORIZONTAL1_DASH_DOT_DASH": "LineHorizontal1DashDotDash",
        "LINE_HORIZONTAL1_DASHES": "LineHorizontal1Dashes",
        "LINE_HORIZONTAL1_DOT": "LineHorizontal1Dot",
        "LINE_HORIZONTAL2_DASHES_SOLID": "LineHorizontal2DashesSolid",
        "LINE_HORIZONTAL3": "LineHorizontal3",
        "LINE_HORIZONTAL4": "LineHorizontal4",
        "LINE_HORIZONTAL4_SEARCH": "LineHorizontal4Search",
        "LINE_HORIZONTAL5": "LineHorizontal5",
        "LINE_HORIZONTAL5_ERROR": "LineHorizontal5Error",
        "LINE_STYLE": "LineStyle",
        "LINE_STYLE_SKETCH": "LineStyleSketch",
        "LINE_THICKNESS": "LineThickness",
        "LINK": "Link",
        "LINK_ADD": "LinkAdd",
        "LINK_DISMISS": "LinkDismiss",
        "LINK_EDIT": "LinkEdit",
        "LINK_MULTIPLE": "LinkMultiple",
        "LINK_PERSON": "LinkPerson",
        "LINK_SETTINGS": "LinkSettings",
        "LINK_SQUARE": "LinkSquare",
        "LINK_TOOLBOX": "LinkToolbox",
        "LIST": "List",
        "LIST_BAR": "ListBar",
        "LIST_BAR_TREE": "ListBarTree",
        "LIST_BAR_TREE_OFFSET": "ListBarTreeOffset",
        "LIST_R_T_L": "ListRTL",
        "LIVE": "Live",
        "LIVE_OFF": "LiveOff",
        "LOCAL_LANGUAGE": "LocalLanguage",
        "LOCATION": "Location",
        "LOCATION_ADD": "LocationAdd",
        "LOCATION_ADD_LEFT": "LocationAddLeft",
        "LOCATION_ADD_RIGHT": "LocationAddRight",
        "LOCATION_ADD_UP": "LocationAddUp",
        "LOCATION_ARROW": "LocationArrow",
        "LOCATION_ARROW_LEFT": "LocationArrowLeft",
        "LOCATION_ARROW_RIGHT": "LocationArrowRight",
        "LOCATION_ARROW_UP": "LocationArrowUp",
        "LOCATION_CHECKMARK": "LocationCheckmark",
        "LOCATION_DISMISS": "LocationDismiss",
        "LOCATION_LIVE": "LocationLive",
        "LOCATION_OFF": "LocationOff",
        "LOCATION_RIPPLE": "LocationRipple",
        "LOCATION_SETTINGS": "LocationSettings",
        "LOCATION_TARGET_SQUARE": "LocationTargetSquare",
        "LOCK_CLOSED": "LockClosed",
        "LOCK_CLOSED_KEY": "LockClosedKey",
        "LOCK_CLOSED_RIBBON": "LockClosedRibbon",
        "LOCK_MULTIPLE": "LockMultiple",
        "LOCK_OPEN": "LockOpen",
        "LOCK_SHIELD": "LockShield",
        "LOTTERY": "Lottery",
        "LUGGAGE": "Luggage",
        "MAIL": "Mail",
        "MAIL_ADD": "MailAdd",
        "MAIL_ALERT": "MailAlert",
        "MAIL_ALL_READ": "MailAllRead",
        "MAIL_ALL_UNREAD": "MailAllUnread",
        "MAIL_ARROW_CLOCKWISE": "MailArrowClockwise",
        "MAIL_ARROW_DOUBLE_BACK": "MailArrowDoubleBack",
        "MAIL_ARROW_DOWN": "MailArrowDown",
        "MAIL_ARROW_FORWARD": "MailArrowForward",
        "MAIL_ARROW_UP": "MailArrowUp",
        "MAIL_ATTACH": "MailAttach",
        "MAILBOX": "Mailbox",
        "MAIL_CHECKMARK": "MailCheckmark",
        "MAIL_CLOCK": "MailClock",
        "MAIL_COPY": "MailCopy",
        "MAIL_DATA_BAR": "MailDataBar",
        "MAIL_DISMISS": "MailDismiss",
        "MAIL_EDIT": "MailEdit",
        "MAIL_ERROR": "MailError",
        "MAIL_FISH_HOOK": "MailFishHook",
        "MAIL_INBOX": "MailInbox",
        "MAIL_INBOX_ADD": "MailInboxAdd",
        "MAIL_INBOX_ALL": "MailInboxAll",
        "MAIL_INBOX_ARROW_DOWN": "MailInboxArrowDown",
        "MAIL_INBOX_ARROW_RIGHT": "MailInboxArrowRight",
        "MAIL_INBOX_ARROW_UP": "MailInboxArrowUp",
        "MAIL_INBOX_CHECKMARK": "MailInboxCheckmark",
        "MAIL_INBOX_DISMISS": "MailInboxDismiss",
        "MAIL_INBOX_PERSON": "MailInboxPerson",
        "MAIL_LINK": "MailLink",
        "MAIL_LIST": "MailList",
        "MAIL_MULTIPLE": "MailMultiple",
        "MAIL_OFF": "MailOff",
        "MAIL_OPEN_PERSON": "MailOpenPerson",
        "MAIL_PAUSE": "MailPause",
        "MAIL_PROHIBITED": "MailProhibited",
        "MAIL_READ": "MailRead",
        "MAIL_READ_BRIEFCASE": "MailReadBriefcase",
        "MAIL_READ_MULTIPLE": "MailReadMultiple",
        "MAIL_REWIND": "MailRewind",
        "MAIL_SETTINGS": "MailSettings",
        "MAIL_SHIELD": "MailShield",
        "MAIL_TEMPLATE": "MailTemplate",
        "MAIL_UNREAD": "MailUnread",
        "MAIL_WARNING": "MailWarning",
        "MAP": "Map",
        "MAP_DRIVE": "MapDrive",
        "MARKDOWN": "Markdown",
        "MATCH_APP_LAYOUT": "MatchAppLayout",
        "MATH_FORMAT_LINEAR": "MathFormatLinear",
        "MATH_FORMAT_PROFESSIONAL": "MathFormatProfessional",
        "MATH_FORMULA": "MathFormula",
        "MATH_FORMULA_SPARKLE": "MathFormulaSparkle",
        "MATH_SYMBOLS": "MathSymbols",
        "MAXIMIZE": "Maximize",
        "MEET_NOW": "MeetNow",
        "MEGAPHONE": "Megaphone",
        "MEGAPHONE_CIRCLE": "MegaphoneCircle",
        "MEGAPHONE_LOUD": "MegaphoneLoud",
        "MEGAPHONE_OFF": "MegaphoneOff",
        "MEMORY": "Memory",
        "MENTION": "Mention",
        "MENTION_ARROW_DOWN": "MentionArrowDown",
        "MENTION_BRACKETS": "MentionBrackets",
        "MERGE": "Merge",
        "MIC": "Mic",
        "MIC_LINK": "MicLink",
        "MIC_OFF": "MicOff",
        "MIC_PROHIBITED": "MicProhibited",
        "MIC_PULSE": "MicPulse",
        "MIC_PULSE_OFF": "MicPulseOff",
        "MIC_RECORD": "MicRecord",
        "MICROSCOPE": "Microscope",
        "MICROWAVE": "Microwave",
        "MIC_SETTINGS": "MicSettings",
        "MIC_SPARKLE": "MicSparkle",
        "MIC_SYNC": "MicSync",
        "MIDI": "Midi",
        "MOBILE_OPTIMIZED": "MobileOptimized",
        "MOLD": "Mold",
        "MOLECULE": "Molecule",
        "MONEY": "Money",
        "MONEY_CALCULATOR": "MoneyCalculator",
        "MONEY_DISMISS": "MoneyDismiss",
        "MONEY_HAND": "MoneyHand",
        "MONEY_OFF": "MoneyOff",
        "MONEY_SETTINGS": "MoneySettings",
        "MORE_CIRCLE": "MoreCircle",
        "MORE_HORIZONTAL": "MoreHorizontal",
        "MORE_VERTICAL": "MoreVertical",
        "MOUNTAIN_LOCATION_BOTTOM": "MountainLocationBottom",
        "MOUNTAIN_LOCATION_TOP": "MountainLocationTop",
        "MOUNTAIN_TRAIL": "MountainTrail",
        "MOVIESAND_T_V": "MoviesandTV",
        "MULTIPLIER1_2X": "Multiplier1_2x",
        "MULTIPLIER1_5X": "Multiplier1_5x",
        "MULTIPLIER1_8X": "Multiplier1_8x",
        "MULTIPLIER1X": "Multiplier1x",
        "MULTIPLIER2X": "Multiplier2x",
        "MULTIPLIER_5X": "Multiplier_5x",
        "MULTISELECT_L_T_R": "MultiselectLTR",
        "MULTISELECT_R_T_L": "MultiselectRTL",
        "MUSIC_NOTE1": "MusicNote1",
        "MUSIC_NOTE2": "MusicNote2",
        "MUSIC_NOTE2_PLAY": "MusicNote2Play",
        "MUSIC_NOTE_OFF1": "MusicNoteOff1",
        "MUSIC_NOTE_OFF2": "MusicNoteOff2",
        "MY_LOCATION": "MyLocation",
        "NAVIGATION": "Navigation",
        "NAVIGATION_BRIEFCASE": "NavigationBriefcase",
        "NAVIGATION_LOCATION_TARGET": "NavigationLocationTarget",
        "NAVIGATION_PERSON": "NavigationPerson",
        "NAVIGATION_PLAY": "NavigationPlay",
        "NAVIGATION_UNREAD": "NavigationUnread",
        "NETWORK_ADAPTER": "NetworkAdapter",
        "NETWORK_CHECK": "NetworkCheck",
        "NEW": "New",
        "NEWS": "News",
        "NEXT": "Next",
        "NEXT_FRAME": "NextFrame",
        "NOTE": "Note",
        "NOTE_ADD": "NoteAdd",
        "NOTEBOOK": "Notebook",
        "NOTEBOOK_ADD": "NotebookAdd",
        "NOTEBOOK_ARROW_CURVE_DOWN": "NotebookArrowCurveDown",
        "NOTEBOOK_ERROR": "NotebookError",
        "NOTEBOOK_EYE": "NotebookEye",
        "NOTEBOOK_LIGHTNING": "NotebookLightning",
        "NOTEBOOK_QUESTION_MARK": "NotebookQuestionMark",
        "NOTEBOOK_SECTION": "NotebookSection",
        "NOTEBOOK_SECTION_ARROW_RIGHT": "NotebookSectionArrowRight",
        "NOTEBOOK_SUBSECTION": "NotebookSubsection",
        "NOTEBOOK_SYNC": "NotebookSync",
        "NOTE_EDIT": "NoteEdit",
        "NOTEPAD": "Notepad",
        "NOTEPAD_EDIT": "NotepadEdit",
        "NOTEPAD_PERSON": "NotepadPerson",
        "NOTEPAD_PERSON_OFF": "NotepadPersonOff",
        "NOTEPAD_SPARKLE": "NotepadSparkle",
        "NOTE_PIN": "NotePin",
        "NUMBER_CIRCLE0": "NumberCircle0",
        "NUMBER_CIRCLE1": "NumberCircle1",
        "NUMBER_CIRCLE2": "NumberCircle2",
        "NUMBER_CIRCLE3": "NumberCircle3",
        "NUMBER_CIRCLE4": "NumberCircle4",
        "NUMBER_CIRCLE5": "NumberCircle5",
        "NUMBER_CIRCLE6": "NumberCircle6",
        "NUMBER_CIRCLE7": "NumberCircle7",
        "NUMBER_CIRCLE8": "NumberCircle8",
        "NUMBER_CIRCLE9": "NumberCircle9",
        "NUMBER_ROW": "NumberRow",
        "NUMBER_SYMBOL": "NumberSymbol",
        "NUMBER_SYMBOL_DISMISS": "NumberSymbolDismiss",
        "NUMBER_SYMBOL_SQUARE": "NumberSymbolSquare",
        "OPEN": "Open",
        "OPEN_FOLDER": "OpenFolder",
        "OPEN_OFF": "OpenOff",
        "OPTIONS": "Options",
        "ORGANIZATION": "Organization",
        "ORGANIZATION_HORIZONTAL": "OrganizationHorizontal",
        "ORIENTATION": "Orientation",
        "OVAL": "Oval",
        "OVEN": "Oven",
        "PADDING_DOWN": "PaddingDown",
        "PADDING_LEFT": "PaddingLeft",
        "PADDING_RIGHT": "PaddingRight",
        "PADDING_TOP": "PaddingTop",
        "PAGE_FIT": "PageFit",
        "PAINT_BRUSH": "PaintBrush",
        "PAINT_BRUSH_ARROW_DOWN": "PaintBrushArrowDown",
        "PAINT_BRUSH_ARROW_UP": "PaintBrushArrowUp",
        "PAINT_BRUSH_SPARKLE": "PaintBrushSparkle",
        "PAINT_BRUSH_SUBTRACT": "PaintBrushSubtract",
        "PAINT_BUCKET": "PaintBucket",
        "PAINT_BUCKET_BRUSH": "PaintBucketBrush",
        "PAIR": "Pair",
        "PANEL_BOTTOM": "PanelBottom",
        "PANEL_BOTTOM_CONTRACT": "PanelBottomContract",
        "PANEL_BOTTOM_EXPAND": "PanelBottomExpand",
        "PANEL_LEFT": "PanelLeft",
        "PANEL_LEFT_ADD": "PanelLeftAdd",
        "PANEL_LEFT_CONTRACT": "PanelLeftContract",
        "PANEL_LEFT_EXPAND": "PanelLeftExpand",
        "PANEL_LEFT_HEADER": "PanelLeftHeader",
        "PANEL_LEFT_HEADER_ADD": "PanelLeftHeaderAdd",
        "PANEL_LEFT_HEADER_KEY": "PanelLeftHeaderKey",
        "PANEL_LEFT_KEY": "PanelLeftKey",
        "PANEL_LEFT_TEXT": "PanelLeftText",
        "PANEL_LEFT_TEXT_ADD": "PanelLeftTextAdd",
        "PANEL_LEFT_TEXT_DISMISS": "PanelLeftTextDismiss",
        "PANEL_RIGHT": "PanelRight",
        "PANEL_RIGHT_ADD": "PanelRightAdd",
        "PANEL_RIGHT_CONTRACT": "PanelRightContract",
        "PANEL_RIGHT_CURSOR": "PanelRightCursor",
        "PANEL_RIGHT_EXPAND": "PanelRightExpand",
        "PANEL_RIGHT_GALLERY": "PanelRightGallery",
        "PANEL_SEPARATE_WINDOW": "PanelSeparateWindow",
        "PANEL_TOP_CONTRACT": "PanelTopContract",
        "PANEL_TOP_EXPAND": "PanelTopExpand",
        "PANEL_TOP_GALLERY": "PanelTopGallery",
        "PASSWORD": "Password",
        "PASSWORD_CLOCK": "PasswordClock",
        "PATCH": "Patch",
        "PATIENT": "Patient",
        "PAUSE": "Pause",
        "PAUSE_CIRCLE": "PauseCircle",
        "PAUSE_OFF": "PauseOff",
        "PAUSE_SETTINGS": "PauseSettings",
        "PAYMENT": "Payment",
        "PAYMENT_WIRELESS": "PaymentWireless",
        "PEN": "Pen",
        "PEN_DISMISS": "PenDismiss",
        "PEN_OFF": "PenOff",
        "PEN_PROHIBITED": "PenProhibited",
        "PEN_SPARKLE": "PenSparkle",
        "PEN_SYNC": "PenSync",
        "PENTAGON": "Pentagon",
        "PEOPLE": "People",
        "PEOPLE_ADD": "PeopleAdd",
        "PEOPLE_AUDIENCE": "PeopleAudience",
        "PEOPLE_CALL": "PeopleCall",
        "PEOPLE_CHAT": "PeopleChat",
        "PEOPLE_CHECKMARK": "PeopleCheckmark",
        "PEOPLE_COMMUNICATION": "PeopleCommunication",
        "PEOPLE_COMMUNITY": "PeopleCommunity",
        "PEOPLE_COMMUNITY_ADD": "PeopleCommunityAdd",
        "PEOPLE_EDIT": "PeopleEdit",
        "PEOPLE_ERROR": "PeopleError",
        "PEOPLE_EYE": "PeopleEye",
        "PEOPLE_INTERWOVEN": "PeopleInterwoven",
        "PEOPLE_LINK": "PeopleLink",
        "PEOPLE_LIST": "PeopleList",
        "PEOPLE_LOCK": "PeopleLock",
        "PEOPLE_MONEY": "PeopleMoney",
        "PEOPLE_PROHIBITED": "PeopleProhibited",
        "PEOPLE_QUEUE": "PeopleQueue",
        "PEOPLE_SEARCH": "PeopleSearch",
        "PEOPLE_SETTINGS": "PeopleSettings",
        "PEOPLE_STAR": "PeopleStar",
        "PEOPLE_SUBTRACT": "PeopleSubtract",
        "PEOPLE_SWAP": "PeopleSwap",
        "PEOPLE_SYNC": "PeopleSync",
        "PEOPLE_TEAM": "PeopleTeam",
        "PEOPLE_TEAM_ADD": "PeopleTeamAdd",
        "PEOPLE_TEAM_DELETE": "PeopleTeamDelete",
        "PEOPLE_TEAM_TOOLBOX": "PeopleTeamToolbox",
        "PEOPLE_TOOLBOX": "PeopleToolbox",
        "PERSON": "Person",
        "PERSON5": "Person5",
        "PERSON6": "Person6",
        "PERSON_ACCOUNT": "PersonAccount",
        "PERSON_ACCOUNTS": "PersonAccounts",
        "PERSON_ADD": "PersonAdd",
        "PERSON_ALERT": "PersonAlert",
        "PERSON_ALERT_OFF": "PersonAlertOff",
        "PERSON_ARROW_BACK": "PersonArrowBack",
        "PERSON_ARROW_LEFT": "PersonArrowLeft",
        "PERSON_ARROW_RIGHT": "PersonArrowRight",
        "PERSON_AVAILABLE": "PersonAvailable",
        "PERSON_BOARD": "PersonBoard",
        "PERSON_BOARD_ADD": "PersonBoardAdd",
        "PERSON_BRIEFCASE": "PersonBriefcase",
        "PERSON_CALL": "PersonCall",
        "PERSON_CHAT": "PersonChat",
        "PERSON_CIRCLE": "PersonCircle",
        "PERSON_CLOCK": "PersonClock",
        "PERSON_DELETE": "PersonDelete",
        "PERSON_DESKTOP": "PersonDesktop",
        "PERSON_EDIT": "PersonEdit",
        "PERSON_ERROR": "PersonError",
        "PERSON_FEEDBACK": "PersonFeedback",
        "PERSON_GUEST": "PersonGuest",
        "PERSON_HEAD_HINT": "PersonHeadHint",
        "PERSON_HEART": "PersonHeart",
        "PERSON_HOME": "PersonHome",
        "PERSON_INFO": "PersonInfo",
        "PERSON_KEY": "PersonKey",
        "PERSON_LIGHTBULB": "PersonLightbulb",
        "PERSON_LIGHTNING": "PersonLightning",
        "PERSON_LINK": "PersonLink",
        "PERSON_LOCK": "PersonLock",
        "PERSON_MAIL": "PersonMail",
        "PERSON_MONEY": "PersonMoney",
        "PERSON_NOTE": "PersonNote",
        "PERSON_PASSKEY": "PersonPasskey",
        "PERSON_PHONE": "PersonPhone",
        "PERSON_PILL": "PersonPill",
        "PERSON_PROHIBITED": "PersonProhibited",
        "PERSON_QUESTION_MARK": "PersonQuestionMark",
        "PERSON_RIBBON": "PersonRibbon",
        "PERSON_RUNNING": "PersonRunning",
        "PERSON_SEARCH": "PersonSearch",
        "PERSON_SETTINGS": "PersonSettings",
        "PERSON_SHIELD": "PersonShield",
        "PERSON_SOUND_SPATIAL": "PersonSoundSpatial",
        "PERSON_SQUARE": "PersonSquare",
        "PERSON_SQUARE_ADD": "PersonSquareAdd",
        "PERSON_SQUARE_CHECKMARK": "PersonSquareCheckmark",
        "PERSON_STANDING": "PersonStanding",
        "PERSON_STAR": "PersonStar",
        "PERSON_STARBURST": "PersonStarburst",
        "PERSON_SUBTRACT": "PersonSubtract",
        "PERSON_SUPPORT": "PersonSupport",
        "PERSON_SWAP": "PersonSwap",
        "PERSON_SYNC": "PersonSync",
        "PERSON_TAG": "PersonTag",
        "PERSON_TENTATIVE": "PersonTentative",
        "PERSON_VOICE": "PersonVoice",
        "PERSON_WALKING": "PersonWalking",
        "PERSON_WARNING": "PersonWarning",
        "PERSON_WRENCH": "PersonWrench",
        "PHONE": "Phone",
        "PHONE_ADD": "PhoneAdd",
        "PHONE_ARROW_RIGHT": "PhoneArrowRight",
        "PHONE_BRIEFCASE": "PhoneBriefcase",
        "PHONE_CHAT": "PhoneChat",
        "PHONE_CHECKMARK": "PhoneCheckmark",
        "PHONE_DESKTOP": "PhoneDesktop",
        "PHONE_DESKTOP_ADD": "PhoneDesktopAdd",
        "PHONE_DISMISS": "PhoneDismiss",
        "PHONE_EDIT": "PhoneEdit",
        "PHONE_ERASER": "PhoneEraser",
        "PHONE_FOOTER_ARROW_DOWN": "PhoneFooterArrowDown",
        "PHONE_HEADER_ARROW_UP": "PhoneHeaderArrowUp",
        "PHONE_KEY": "PhoneKey",
        "PHONE_LAPTOP": "PhoneLaptop",
        "PHONE_LINK_SETUP": "PhoneLinkSetup",
        "PHONE_LOCK": "PhoneLock",
        "PHONE_MULTIPLE": "PhoneMultiple",
        "PHONE_MULTIPLE_SETTINGS": "PhoneMultipleSettings",
        "PHONE_PAGE_HEADER": "PhonePageHeader",
        "PHONE_PAGINATION": "PhonePagination",
        "PHONE_PERSON": "PhonePerson",
        "PHONE_SCREEN_TIME": "PhoneScreenTime",
        "PHONE_SHAKE": "PhoneShake",
        "PHONE_SPAN_IN": "PhoneSpanIn",
        "PHONE_SPAN_OUT": "PhoneSpanOut",
        "PHONE_SPEAKER": "PhoneSpeaker",
        "PHONE_STATUS_BAR": "PhoneStatusBar",
        "PHONE_SUBTRACT": "PhoneSubtract",
        "PHONE_TABLET": "PhoneTablet",
        "PHONE_UPDATE": "PhoneUpdate",
        "PHONE_UPDATE_CHECKMARK": "PhoneUpdateCheckmark",
        "PHONE_VERTICAL_SCROLL": "PhoneVerticalScroll",
        "PHONE_VIBRATE": "PhoneVibrate",
        "PHOTO_FILTER": "PhotoFilter",
        "PI": "Pi",
        "PICTURE_IN_PICTURE": "PictureInPicture",
        "PICTURE_IN_PICTURE_ENTER": "PictureInPictureEnter",
        "PICTURE_IN_PICTURE_EXIT": "PictureInPictureExit",
        "PILL": "Pill",
        "PIN": "Pin",
        "PIN_GLOBE": "PinGlobe",
        "PIN_OFF": "PinOff",
        "PIPELINE": "Pipeline",
        "PIPELINE_ADD": "PipelineAdd",
        "PIPELINE_ARROW_CURVE_DOWN": "PipelineArrowCurveDown",
        "PIPELINE_PLAY": "PipelinePlay",
        "PIVOT": "Pivot",
        "PLANET": "Planet",
        "PLANT_CATTAIL": "PlantCattail",
        "PLANT_GRASS": "PlantGrass",
        "PLANT_RAGWEED": "PlantRagweed",
        "PLAY": "Play",
        "PLAY_CIRCLE": "PlayCircle",
        "PLAY_CIRCLE_HINT": "PlayCircleHint",
        "PLAY_CIRCLE_HINT_HALF": "PlayCircleHintHalf",
        "PLAY_CIRCLE_SPARKLE": "PlayCircleSparkle",
        "PLAYING_CARDS": "PlayingCards",
        "PLAY_MULTIPLE": "PlayMultiple",
        "PLAY_SETTINGS": "PlaySettings",
        "PLUG_CONNECTED": "PlugConnected",
        "PLUG_CONNECTED_ADD": "PlugConnectedAdd",
        "PLUG_CONNECTED_CHECKMARK": "PlugConnectedCheckmark",
        "PLUG_CONNECTED_SETTINGS": "PlugConnectedSettings",
        "PLUG_DISCONNECTED": "PlugDisconnected",
        "POINT_SCAN": "PointScan",
        "POLL": "Poll",
        "POLL_HORIZONTAL": "PollHorizontal",
        "POLL_OFF": "PollOff",
        "PORT_H_D_M_I": "PortHDMI",
        "PORT_MICRO_U_S_B": "PortMicroUSB",
        "PORT_U_S_B_A": "PortUSBA",
        "PORT_U_S_B_C": "PortUSBC",
        "POSITION_BACKWARD": "PositionBackward",
        "POSITION_FORWARD": "PositionForward",
        "POSITION_TO_BACK": "PositionToBack",
        "POSITION_TO_FRONT": "PositionToFront",
        "POWER": "Power",
        "PREDICTIONS": "Predictions",
        "PREMIUM": "Premium",
        "PREMIUM_PERSON": "PremiumPerson",
        "PRESENCE_AVAILABLE": "PresenceAvailable",
        "PRESENCE_AWAY": "PresenceAway",
        "PRESENCE_BLOCKED": "PresenceBlocked",
        "PRESENCE_D_N_D": "PresenceDND",
        "PRESENCE_OFFLINE": "PresenceOffline",
        "PRESENCE_O_O_F": "PresenceOOF",
        "PRESENCE_TENTATIVE": "PresenceTentative",
        "PRESENCE_UNKNOWN": "PresenceUnknown",
        "PRESENTER": "Presenter",
        "PRESENTER_OFF": "PresenterOff",
        "PREVIEW_LINK": "PreviewLink",
        "PREVIOUS": "Previous",
        "PREVIOUS_FRAME": "PreviousFrame",
        "PRINT": "Print",
        "PRINT_ADD": "PrintAdd",
        "PRODUCTION": "Production",
        "PRODUCTION_CHECKMARK": "ProductionCheckmark",
        "PROHIBITED": "Prohibited",
        "PROHIBITED_MULTIPLE": "ProhibitedMultiple",
        "PROHIBITED_NOTE": "ProhibitedNote",
        "PROHIBITED_SMOKING": "ProhibitedSmoking",
        "PROJECTION_SCREEN": "ProjectionScreen",
        "PROJECTION_SCREEN_DISMISS": "ProjectionScreenDismiss",
        "PROJECTION_SCREEN_TEXT": "ProjectionScreenText",
        "PROJECTION_SCREEN_TEXT_SPARKLE": "ProjectionScreenTextSparkle",
        "PROMPT": "Prompt",
        "PROTOCOL_HANDLER": "ProtocolHandler",
        "PULSE": "Pulse",
        "PULSE_SQUARE": "PulseSquare",
        "PUZZLE_CUBE": "PuzzleCube",
        "PUZZLE_CUBE_PIECE": "PuzzleCubePiece",
        "PUZZLE_PIECE": "PuzzlePiece",
        "PUZZLE_PIECE_SHIELD": "PuzzlePieceShield",
        "Q_R_CODE": "QRCode",
        "QUESTION": "Question",
        "QUESTION_CIRCLE": "QuestionCircle",
        "QUIZ": "Quiz",
        "QUIZ_NEW": "QuizNew",
        "RADAR": "Radar",
        "RADAR_CHECKMARK": "RadarCheckmark",
        "RADAR_RECTANGLE_MULTIPLE": "RadarRectangleMultiple",
        "RADIO_BUTTON": "RadioButton",
        "RADIO_BUTTON_OFF": "RadioButtonOff",
        "R_A_M": "RAM",
        "RATING_MATURE": "RatingMature",
        "RATIO_ONE_TO_ONE": "RatioOneToOne",
        "READ_ALOUD": "ReadAloud",
        "READING_LIST": "ReadingList",
        "READING_LIST_ADD": "ReadingListAdd",
        "READING_MODE_MOBILE": "ReadingModeMobile",
        "REAL_ESTATE": "RealEstate",
        "RECEIPT": "Receipt",
        "RECEIPT_ADD": "ReceiptAdd",
        "RECEIPT_BAG": "ReceiptBag",
        "RECEIPT_CUBE": "ReceiptCube",
        "RECEIPT_MONEY": "ReceiptMoney",
        "RECEIPT_PLAY": "ReceiptPlay",
        "RECEIPT_SEARCH": "ReceiptSearch",
        "RECEIPT_SPARKLES": "ReceiptSparkles",
        "RECORD": "Record",
        "RECORD_STOP": "RecordStop",
        "RECTANGLE_LANDSCAPE": "RectangleLandscape",
        "RECTANGLE_LANDSCAPE_HINT_COPY": "RectangleLandscapeHintCopy",
        "RECTANGLE_LANDSCAPE_SPARKLE": "RectangleLandscapeSparkle",
        "RECTANGLE_LANDSCAPE_SYNC": "RectangleLandscapeSync",
        "RECTANGLE_LANDSCAPE_SYNC_OFF": "RectangleLandscapeSyncOff",
        "RECTANGLE_PORTRAIT": "RectanglePortrait",
        "RECTANGLE_PORTRAIT_LOCATION_TARGET": "RectanglePortraitLocationTarget",
        "RECYCLE": "Recycle",
        "REFRIGERATOR": "Refrigerator",
        "REMIX_ADD": "RemixAdd",
        "REMOTE": "Remote",
        "RENAME": "Rename",
        "RENAME_A": "RenameA",
        "RE_ORDER": "ReOrder",
        "RE_ORDER_DOTS_HORIZONTAL": "ReOrderDotsHorizontal",
        "RE_ORDER_DOTS_VERTICAL": "ReOrderDotsVertical",
        "RE_ORDER_VERTICAL": "ReOrderVertical",
        "REPLAY": "Replay",
        "RESIZE": "Resize",
        "RESIZE_IMAGE": "ResizeImage",
        "RESIZE_LARGE": "ResizeLarge",
        "RESIZE_SMALL": "ResizeSmall",
        "RESIZE_TABLE": "ResizeTable",
        "RESIZE_VIDEO": "ResizeVideo",
        "REWARD": "Reward",
        "REWIND": "Rewind",
        "RHOMBUS": "Rhombus",
        "RIBBON": "Ribbon",
        "RIBBON_ADD": "RibbonAdd",
        "RIBBON_OFF": "RibbonOff",
        "RIBBON_STAR": "RibbonStar",
        "ROAD": "Road",
        "ROAD_CONE": "RoadCone",
        "ROCKET": "Rocket",
        "ROTATE_LEFT": "RotateLeft",
        "ROTATE_RIGHT": "RotateRight",
        "ROUTER": "Router",
        "ROW_CHILD": "RowChild",
        "ROW_TRIPLE": "RowTriple",
        "R_S_S": "RSS",
        "RULER": "Ruler",
        "RUN": "Run",
        "SANITIZE": "Sanitize",
        "SAVE": "Save",
        "SAVE_ARROW_RIGHT": "SaveArrowRight",
        "SAVE_COPY": "SaveCopy",
        "SAVE_EDIT": "SaveEdit",
        "SAVE_IMAGE": "SaveImage",
        "SAVE_MULTIPLE": "SaveMultiple",
        "SAVE_SEARCH": "SaveSearch",
        "SAVE_SYNC": "SaveSync",
        "SAVINGS": "Savings",
        "SCALE_FILL": "ScaleFill",
        "SCALE_FIT": "ScaleFit",
        "SCALES": "Scales",
        "SCAN": "Scan",
        "SCAN_CAMERA": "ScanCamera",
        "SCAN_DASH": "ScanDash",
        "SCAN_OBJECT": "ScanObject",
        "SCAN_PERSON": "ScanPerson",
        "SCAN_Q_R_CODE": "ScanQRCode",
        "SCAN_TABLE": "ScanTable",
        "SCAN_TEXT": "ScanText",
        "SCAN_THUMB_UP": "ScanThumbUp",
        "SCAN_THUMB_UP_OFF": "ScanThumbUpOff",
        "SCAN_TYPE": "ScanType",
        "SCAN_TYPE_CHECKMARK": "ScanTypeCheckmark",
        "SCAN_TYPE_OFF": "ScanTypeOff",
        "SCRATCHPAD": "Scratchpad",
        "SCREEN_CUT": "ScreenCut",
        "SCREEN_PERSON": "ScreenPerson",
        "SCREEN_SEARCH": "ScreenSearch",
        "SCREENSHOT": "Screenshot",
        "SCREENSHOT_RECORD": "ScreenshotRecord",
        "SCRIPT": "Script",
        "SEARCH": "Search",
        "SEARCH_INFO": "SearchInfo",
        "SEARCH_SETTINGS": "SearchSettings",
        "SEARCH_SHIELD": "SearchShield",
        "SEARCH_SPARKLE": "SearchSparkle",
        "SEARCH_SQUARE": "SearchSquare",
        "SEARCH_VISUAL": "SearchVisual",
        "SEAT": "Seat",
        "SEAT_ADD": "SeatAdd",
        "SEAT_MULTIPLE_STADIUM": "SeatMultipleStadium",
        "SELECT_ALL_OFF": "SelectAllOff",
        "SELECT_ALL_ON": "SelectAllOn",
        "SELECT_OBJECT": "SelectObject",
        "SELECT_OBJECT_SKEW": "SelectObjectSkew",
        "SELECT_OBJECT_SKEW_DISMISS": "SelectObjectSkewDismiss",
        "SELECT_OBJECT_SKEW_EDIT": "SelectObjectSkewEdit",
        "SEND": "Send",
        "SEND_BEAKER": "SendBeaker",
        "SEND_CLOCK": "SendClock",
        "SEND_COPY": "SendCopy",
        "SEND_PERSON": "SendPerson",
        "SERIAL_PORT": "SerialPort",
        "SERVER": "Server",
        "SERVER_LINK": "ServerLink",
        "SERVER_MULTIPLE": "ServerMultiple",
        "SERVER_PLAY": "ServerPlay",
        "SERVER_SURFACE": "ServerSurface",
        "SERVER_SURFACE_MULTIPLE": "ServerSurfaceMultiple",
        "SERVICE_BELL": "ServiceBell",
        "SETTINGS": "Settings",
        "SETTINGS_CHAT": "SettingsChat",
        "SETTINGS_COG_MULTIPLE": "SettingsCogMultiple",
        "SHAPE_EXCLUDE": "ShapeExclude",
        "SHAPE_INTERSECT": "ShapeIntersect",
        "SHAPE_ORGANIC": "ShapeOrganic",
        "SHAPES": "Shapes",
        "SHAPE_SUBTRACT": "ShapeSubtract",
        "SHAPE_UNION": "ShapeUnion",
        "SHARE": "Share",
        "SHARE_ANDROID": "ShareAndroid",
        "SHARE_CLOSE_TRAY": "ShareCloseTray",
        "SHAREI_O_S": "ShareiOS",
        "SHARE_MULTIPLE": "ShareMultiple",
        "SHARE_SCREEN_PERSON": "ShareScreenPerson",
        "SHARE_SCREEN_PERSON_OVERLAY": "ShareScreenPersonOverlay",
        "SHARE_SCREEN_PERSON_OVERLAY_INSIDE": "ShareScreenPersonOverlayInside",
        "SHARE_SCREEN_PERSON_P": "ShareScreenPersonP",
        "SHARE_SCREEN_START": "ShareScreenStart",
        "SHARE_SCREEN_STOP": "ShareScreenStop",
        "SHIELD": "Shield",
        "SHIELD_ADD": "ShieldAdd",
        "SHIELD_ARROW_RIGHT": "ShieldArrowRight",
        "SHIELD_BADGE": "ShieldBadge",
        "SHIELD_CHECKMARK": "ShieldCheckmark",
        "SHIELD_DISMISS": "ShieldDismiss",
        "SHIELD_DISMISS_SHIELD": "ShieldDismissShield",
        "SHIELD_ERROR": "ShieldError",
        "SHIELD_GLOBE": "ShieldGlobe",
        "SHIELD_KEYHOLE": "ShieldKeyhole",
        "SHIELD_LOCK": "ShieldLock",
        "SHIELD_PERSON": "ShieldPerson",
        "SHIELD_PERSON_ADD": "ShieldPersonAdd",
        "SHIELD_PROHIBITED": "ShieldProhibited",
        "SHIELD_QUESTION": "ShieldQuestion",
        "SHIELD_SETTINGS": "ShieldSettings",
        "SHIELD_TASK": "ShieldTask",
        "SHIFTS": "Shifts",
        "SHIFTS30_MINUTES": "Shifts30Minutes",
        "SHIFTS_ACTIVITY": "ShiftsActivity",
        "SHIFTS_ADD": "ShiftsAdd",
        "SHIFTS_AVAILABILITY": "ShiftsAvailability",
        "SHIFTS_CHECKMARK": "ShiftsCheckmark",
        "SHIFTS_DAY": "ShiftsDay",
        "SHIFTS_OPEN": "ShiftsOpen",
        "SHIFTS_PROHIBITED": "ShiftsProhibited",
        "SHIFTS_QUESTION_MARK": "ShiftsQuestionMark",
        "SHIFTS_TEAM": "ShiftsTeam",
        "SHOPPING_BAG": "ShoppingBag",
        "SHOPPING_BAG_ADD": "ShoppingBagAdd",
        "SHOPPING_BAG_ARROW_LEFT": "ShoppingBagArrowLeft",
        "SHOPPING_BAG_CHECKMARK": "ShoppingBagCheckmark",
        "SHOPPING_BAG_DISMISS": "ShoppingBagDismiss",
        "SHOPPING_BAG_PAUSE": "ShoppingBagPause",
        "SHOPPING_BAG_PERCENT": "ShoppingBagPercent",
        "SHOPPING_BAG_PLAY": "ShoppingBagPlay",
        "SHOPPING_BAG_TAG": "ShoppingBagTag",
        "SHORTPICK": "Shortpick",
        "SHOWERHEAD": "Showerhead",
        "SIDEBAR_SEARCH_L_T_R": "SidebarSearchLTR",
        "SIDEBAR_SEARCH_R_T_L": "SidebarSearchRTL",
        "SIGNATURE": "Signature",
        "SIGN_OUT": "SignOut",
        "S_I_M": "SIM",
        "SINE_WAVE_DOTS": "SineWaveDots",
        "SKIP_BACK10": "SkipBack10",
        "SKIP_BACK15": "SkipBack15",
        "SKIP_FORWARD10": "SkipForward10",
        "SKIP_FORWARD15": "SkipForward15",
        "SKIP_FORWARD30": "SkipForward30",
        "SKIP_FORWARD_TAB": "SkipForwardTab",
        "SLASH_FORWARD": "SlashForward",
        "SLEEP": "Sleep",
        "SLIDE_ADD": "SlideAdd",
        "SLIDE_ARROW_RIGHT": "SlideArrowRight",
        "SLIDE_CONTENT": "SlideContent",
        "SLIDE_ERASER": "SlideEraser",
        "SLIDE_GRID": "SlideGrid",
        "SLIDE_HIDE": "SlideHide",
        "SLIDE_LAYOUT": "SlideLayout",
        "SLIDE_LINK": "SlideLink",
        "SLIDE_MICROPHONE": "SlideMicrophone",
        "SLIDE_MULTIPLE": "SlideMultiple",
        "SLIDE_MULTIPLE_ARROW_RIGHT": "SlideMultipleArrowRight",
        "SLIDE_MULTIPLE_SEARCH": "SlideMultipleSearch",
        "SLIDE_PLAY": "SlidePlay",
        "SLIDE_RECORD": "SlideRecord",
        "SLIDE_SEARCH": "SlideSearch",
        "SLIDE_SETTINGS": "SlideSettings",
        "SLIDE_SIZE": "SlideSize",
        "SLIDE_TEXT": "SlideText",
        "SLIDE_TEXT_CALL": "SlideTextCall",
        "SLIDE_TEXT_CURSOR": "SlideTextCursor",
        "SLIDE_TEXT_EDIT": "SlideTextEdit",
        "SLIDE_TEXT_MULTIPLE": "SlideTextMultiple",
        "SLIDE_TEXT_PERSON": "SlideTextPerson",
        "SLIDE_TEXT_SPARKLE": "SlideTextSparkle",
        "SLIDE_TEXT_TITLE": "SlideTextTitle",
        "SLIDE_TEXT_TITLE_ADD": "SlideTextTitleAdd",
        "SLIDE_TEXT_TITLE_CHECKMARK": "SlideTextTitleCheckmark",
        "SLIDE_TEXT_TITLE_EDIT": "SlideTextTitleEdit",
        "SLIDE_TOPIC_ADD": "SlideTopicAdd",
        "SLIDE_TRANSITION": "SlideTransition",
        "SMARTWATCH": "Smartwatch",
        "SMARTWATCH_DOT": "SmartwatchDot",
        "SNOOZE": "Snooze",
        "SOUND_SOURCE": "SoundSource",
        "SOUND_WAVE_CIRCLE": "SoundWaveCircle",
        "SOUND_WAVE_CIRCLE_ADD": "SoundWaveCircleAdd",
        "SOUND_WAVE_CIRCLE_SPARKLE": "SoundWaveCircleSparkle",
        "SOUND_WAVE_CIRCLE_SUBTRACT": "SoundWaveCircleSubtract",
        "SPACE3_D": "Space3D",
        "SPACEBAR": "Spacebar",
        "SPARKLE": "Sparkle",
        "SPARKLE_ACTION": "SparkleAction",
        "SPARKLE_CIRCLE": "SparkleCircle",
        "SPARKLE_INFO": "SparkleInfo",
        "SPATULA_SPOON": "SpatulaSpoon",
        "SPEAKER0": "Speaker0",
        "SPEAKER1": "Speaker1",
        "SPEAKER2": "Speaker2",
        "SPEAKER_BLUETOOTH": "SpeakerBluetooth",
        "SPEAKER_BOX": "SpeakerBox",
        "SPEAKER_EDIT": "SpeakerEdit",
        "SPEAKER_MUTE": "SpeakerMute",
        "SPEAKER_OFF": "SpeakerOff",
        "SPEAKER_SETTINGS": "SpeakerSettings",
        "SPEAKER_U_S_B": "SpeakerUSB",
        "SPINNERI_O_S": "SpinneriOS",
        "SPLIT_HINT": "SplitHint",
        "SPLIT_HORIZONTAL": "SplitHorizontal",
        "SPLIT_VERTICAL": "SplitVertical",
        "SPORT": "Sport",
        "SPORT_AMERICAN_FOOTBALL": "SportAmericanFootball",
        "SPORT_BASEBALL": "SportBaseball",
        "SPORT_BASKETBALL": "SportBasketball",
        "SPORT_CRICKET_BALL": "SportCricketBall",
        "SPORT_CRICKET_BAT": "SportCricketBat",
        "SPORT_HOCKEY": "SportHockey",
        "SPORT_SOCCER": "SportSoccer",
        "SPRAY_CAN": "SprayCan",
        "SQUARE": "Square",
        "SQUARE_ADD": "SquareAdd",
        "SQUARE_ARROW_FORWARD": "SquareArrowForward",
        "SQUARE_DISMISS": "SquareDismiss",
        "SQUARE_DOVETAIL_JOINT": "SquareDovetailJoint",
        "SQUARE_ERASER": "SquareEraser",
        "SQUARE_HINT": "SquareHint",
        "SQUARE_HINT_APPS": "SquareHintApps",
        "SQUARE_HINT_ARROW_BACK": "SquareHintArrowBack",
        "SQUARE_HINT_HEXAGON": "SquareHintHexagon",
        "SQUARE_HINT_SPARKLES": "SquareHintSparkles",
        "SQUARE_MULTIPLE": "SquareMultiple",
        "SQUARE_SHADOW": "SquareShadow",
        "SQUARES_NESTED": "SquaresNested",
        "SQUARE_TEXT_ARROW_REPEAT_ALL": "SquareTextArrowRepeatAll",
        "STACK": "Stack",
        "STACK_ADD": "StackAdd",
        "STACK_ARROW_FORWARD": "StackArrowForward",
        "STACK_OFF": "StackOff",
        "STACK_STAR": "StackStar",
        "STACK_VERTICAL": "StackVertical",
        "STAR": "Star",
        "STAR_ADD": "StarAdd",
        "STAR_ARROW_BACK": "StarArrowBack",
        "STAR_ARROW_RIGHT_END": "StarArrowRightEnd",
        "STAR_ARROW_RIGHT_START": "StarArrowRightStart",
        "STAR_CHECKMARK": "StarCheckmark",
        "STAR_DISMISS": "StarDismiss",
        "STAR_EDIT": "StarEdit",
        "STAR_EMPHASIS": "StarEmphasis",
        "STAR_FILLED": "StarFilled",
        "STAR_HALF": "StarHalf",
        "STAR_LINE_HORIZONTAL3": "StarLineHorizontal3",
        "STAR_OFF": "StarOff",
        "STAR_ONE_QUARTER": "StarOneQuarter",
        "STAR_OUTLINE": "StarOutline",
        "STAR_PROHIBITED": "StarProhibited",
        "STAR_SETTINGS": "StarSettings",
        "STAR_THREE_QUARTER": "StarThreeQuarter",
        "STATUS": "Status",
        "STEP": "Step",
        "STEPS": "Steps",
        "STETHOSCOPE": "Stethoscope",
        "STICKER": "Sticker",
        "STICKER_ADD": "StickerAdd",
        "STOP": "Stop",
        "STORAGE": "Storage",
        "STORE_MICROSOFT": "StoreMicrosoft",
        "STOVE": "Stove",
        "STREAM": "Stream",
        "STREAM_INPUT": "StreamInput",
        "STREAM_INPUT_OUTPUT": "StreamInputOutput",
        "STREAM_OUTPUT": "StreamOutput",
        "STREET_SIGN": "StreetSign",
        "STYLE_GUIDE": "StyleGuide",
        "SUB_GRID": "SubGrid",
        "SUBTITLES": "Subtitles",
        "SUBTRACT": "Subtract",
        "SUBTRACT_CIRCLE": "SubtractCircle",
        "SUBTRACT_CIRCLE_ARROW_BACK": "SubtractCircleArrowBack",
        "SUBTRACT_CIRCLE_ARROW_FORWARD": "SubtractCircleArrowForward",
        "SUBTRACT_PARENTHESES": "SubtractParentheses",
        "SUBTRACT_SQUARE": "SubtractSquare",
        "SUBTRACT_SQUARE_MULTIPLE": "SubtractSquareMultiple",
        "SURFACE_EARBUDS": "SurfaceEarbuds",
        "SURFACE_HUB": "SurfaceHub",
        "SWIMMING_POOL": "SwimmingPool",
        "SWIPE_DOWN": "SwipeDown",
        "SWIPE_RIGHT": "SwipeRight",
        "SWIPE_UP": "SwipeUp",
        "SYMBOLS": "Symbols",
        "SYNC_OFF": "SyncOff",
        "SYRINGE": "Syringe",
        "SYSTEM": "System",
        "TAB": "Tab",
        "TAB_ADD": "TabAdd",
        "TAB_ARROW_LEFT": "TabArrowLeft",
        "TAB_DESKTOP": "TabDesktop",
        "TAB_DESKTOP_ARROW_CLOCKWISE": "TabDesktopArrowClockwise",
        "TAB_DESKTOP_ARROW_LEFT": "TabDesktopArrowLeft",
        "TAB_DESKTOP_BOTTOM": "TabDesktopBottom",
        "TAB_DESKTOP_CLOCK": "TabDesktopClock",
        "TAB_DESKTOP_COPY": "TabDesktopCopy",
        "TAB_DESKTOP_IMAGE": "TabDesktopImage",
        "TAB_DESKTOP_LINK": "TabDesktopLink",
        "TAB_DESKTOP_MULTIPLE": "TabDesktopMultiple",
        "TAB_DESKTOP_MULTIPLE_ADD": "TabDesktopMultipleAdd",
        "TAB_DESKTOP_MULTIPLE_BOTTOM": "TabDesktopMultipleBottom",
        "TAB_DESKTOP_MULTIPLE_SPARKLE": "TabDesktopMultipleSparkle",
        "TAB_DESKTOP_NEW_PAGE": "TabDesktopNewPage",
        "TAB_DESKTOP_SEARCH": "TabDesktopSearch",
        "TAB_GROUP": "TabGroup",
        "TAB_IN_PRIVATE": "TabInPrivate",
        "TAB_IN_PRIVATE_ACCOUNT": "TabInPrivateAccount",
        "TABLE": "Table",
        "TABLE_ADD": "TableAdd",
        "TABLE_ALT_TEXT": "TableAltText",
        "TABLE_ARROW_REPEAT_ALL": "TableArrowRepeatAll",
        "TABLE_ARROW_UP": "TableArrowUp",
        "TABLE_BOTTOM_ROW": "TableBottomRow",
        "TABLE_CALCULATOR": "TableCalculator",
        "TABLE_CELL_ADD": "TableCellAdd",
        "TABLE_CELL_CENTER": "TableCellCenter",
        "TABLE_CELL_CENTER_ARROW_REPEAT_ALL": "TableCellCenterArrowRepeatAll",
        "TABLE_CELL_CENTER_EDIT": "TableCellCenterEdit",
        "TABLE_CELL_CENTER_LINK": "TableCellCenterLink",
        "TABLE_CELL_CENTER_SEARCH": "TableCellCenterSearch",
        "TABLE_CELL_EDIT": "TableCellEdit",
        "TABLE_CELLS_MERGE": "TableCellsMerge",
        "TABLE_CELLS_SPLIT": "TableCellsSplit",
        "TABLE_CHECKER": "TableChecker",
        "TABLE_COLUMN_TOP_BOTTOM": "TableColumnTopBottom",
        "TABLE_COLUMN_TOP_BOTTOM_ARROW_REPEAT_ALL": "TableColumnTopBottomArrowRepeatAll",
        "TABLE_COLUMN_TOP_BOTTOM_EDIT": "TableColumnTopBottomEdit",
        "TABLE_COLUMN_TOP_BOTTOM_LINK": "TableColumnTopBottomLink",
        "TABLE_COLUMN_TOP_BOTTOM_SEARCH": "TableColumnTopBottomSearch",
        "TABLE_COPY": "TableCopy",
        "TABLE_CURSOR": "TableCursor",
        "TABLE_DELETE_COLUMN": "TableDeleteColumn",
        "TABLE_DELETE_ROW": "TableDeleteRow",
        "TABLE_DISMISS": "TableDismiss",
        "TABLE_EDIT": "TableEdit",
        "TABLE_FREEZE_COLUMN": "TableFreezeColumn",
        "TABLE_FREEZE_COLUMN_AND_ROW": "TableFreezeColumnAndRow",
        "TABLE_FREEZE_COLUMN_AND_ROW_DISMISS": "TableFreezeColumnAndRowDismiss",
        "TABLE_FREEZE_COLUMN_AND_ROW_TEMP_L_T_R": "TableFreezeColumnAndRowTempLTR",
        "TABLE_FREEZE_COLUMN_AND_ROW_TEMP_R_T_L": "TableFreezeColumnAndRowTempRTL",
        "TABLE_FREEZE_COLUMN_DISMISS": "TableFreezeColumnDismiss",
        "TABLE_FREEZE_COLUMN_TEMP_L_T_R": "TableFreezeColumnTempLTR",
        "TABLE_FREEZE_COLUMN_TEMP_R_T_L": "TableFreezeColumnTempRTL",
        "TABLE_FREEZE_ROW": "TableFreezeRow",
        "TABLE_FREEZE_ROW_DISMISS": "TableFreezeRowDismiss",
        "TABLE_IMAGE": "TableImage",
        "TABLE_INSERT_COLUMN": "TableInsertColumn",
        "TABLE_INSERT_ROW": "TableInsertRow",
        "TABLE_LIGHTNING": "TableLightning",
        "TABLE_LINK": "TableLink",
        "TABLE_LOCK": "TableLock",
        "TABLE_MOVE_ABOVE": "TableMoveAbove",
        "TABLE_MOVE_BELOW": "TableMoveBelow",
        "TABLE_MOVE_LEFT": "TableMoveLeft",
        "TABLE_MOVE_RIGHT": "TableMoveRight",
        "TABLE_MULTIPLE": "TableMultiple",
        "TABLE_OFFSET": "TableOffset",
        "TABLE_OFFSET_ADD": "TableOffsetAdd",
        "TABLE_OFFSET_LESS_THAN_OR_EQUAL_TO": "TableOffsetLessThanOrEqualTo",
        "TABLE_OFFSET_SETTINGS": "TableOffsetSettings",
        "TABLE_PICNIC": "TablePicnic",
        "TABLE_RESIZE_COLUMN": "TableResizeColumn",
        "TABLE_RESIZE_ROW": "TableResizeRow",
        "TABLE_SEARCH": "TableSearch",
        "TABLE_SETTINGS": "TableSettings",
        "TABLE_SIMPLE": "TableSimple",
        "TABLE_SIMPLE_CHECKMARK": "TableSimpleCheckmark",
        "TABLE_SIMPLE_EXCLUDE": "TableSimpleExclude",
        "TABLE_SIMPLE_INCLUDE": "TableSimpleInclude",
        "TABLE_SIMPLE_MULTIPLE": "TableSimpleMultiple",
        "TABLE_SPARKLE": "TableSparkle",
        "TABLE_SPLIT": "TableSplit",
        "TABLE_STACK_ABOVE": "TableStackAbove",
        "TABLE_STACK_BELOW": "TableStackBelow",
        "TABLE_STACK_LEFT": "TableStackLeft",
        "TABLE_STACK_RIGHT": "TableStackRight",
        "TABLE_SWITCH": "TableSwitch",
        "TABLET": "Tablet",
        "TABLET_LAPTOP": "TabletLaptop",
        "TABLET_SPEAKER": "TabletSpeaker",
        "TAB_PROHIBITED": "TabProhibited",
        "TABS": "Tabs",
        "TAB_SHIELD_DISMISS": "TabShieldDismiss",
        "TAG": "Tag",
        "TAG_ADD": "TagAdd",
        "TAG_CIRCLE": "TagCircle",
        "TAG_DISMISS": "TagDismiss",
        "TAG_EDIT": "TagEdit",
        "TAG_ERROR": "TagError",
        "TAG_LOCK": "TagLock",
        "TAG_MULTIPLE": "TagMultiple",
        "TAG_OFF": "TagOff",
        "TAG_PERCENT": "TagPercent",
        "TAG_QUESTION_MARK": "TagQuestionMark",
        "TAG_RESET": "TagReset",
        "TAG_SEARCH": "TagSearch",
        "TAP_DOUBLE": "TapDouble",
        "TAP_SINGLE": "TapSingle",
        "TARGET": "Target",
        "TARGET_ADD": "TargetAdd",
        "TARGET_ARROW": "TargetArrow",
        "TARGET_DISMISS": "TargetDismiss",
        "TARGET_EDIT": "TargetEdit",
        "TARGET_SPARKLE": "TargetSparkle",
        "TASK_LIST_ADD": "TaskListAdd",
        "TASK_LIST_L_T_R": "TaskListLTR",
        "TASK_LIST_R_T_L": "TaskListRTL",
        "TASK_LIST_SQUARE_ADD": "TaskListSquareAdd",
        "TASK_LIST_SQUARE_DATABASE": "TaskListSquareDatabase",
        "TASK_LIST_SQUARE_L_T_R": "TaskListSquareLTR",
        "TASK_LIST_SQUARE_PERSON": "TaskListSquarePerson",
        "TASK_LIST_SQUARE_R_T_L": "TaskListSquareRTL",
        "TASK_LIST_SQUARE_SETTINGS": "TaskListSquareSettings",
        "TASK_LIST_SQUARE_SPARKLE": "TaskListSquareSparkle",
        "TASKS_APP": "TasksApp",
        "TEACHING": "Teaching",
        "TEARDROP_BOTTOM_RIGHT": "TeardropBottomRight",
        "TEDDY": "Teddy",
        "TEMPERATURE": "Temperature",
        "TEMPERATURE_DEGREE_CELSIUS": "TemperatureDegreeCelsius",
        "TEMPERATURE_DEGREE_FAHRENHEIT": "TemperatureDegreeFahrenheit",
        "TENT": "Tent",
        "TETRIS_APP": "TetrisApp",
        "TEXT": "Text",
        "TEXT_BOLD": "TextBold",
        "TEXT_DESCRIPTION": "TextDescription",
        "TEXT_DESCRIPTION_L_T_R": "TextDescriptionLTR",
        "TEXT_DESCRIPTION_R_T_L": "TextDescriptionRTL",
        "TEXT_PROOFING_TOOLS": "TextProofingTools",
        "TEXT_PROOFING_TOOLS_ABC": "TextProofingToolsAbc",
        "TEXT_PROOFING_TOOLS_GA_NA_DA": "TextProofingToolsGaNaDa",
        "TEXT_PROOFING_TOOLS_ZI": "TextProofingToolsZi",
        "THINKING": "Thinking",
        "THUMB_DISLIKE": "ThumbDislike",
        "THUMB_LIKE": "ThumbLike",
        "THUMB_LIKE_DISLIKE": "ThumbLikeDislike",
        "TICKET_DIAGONAL": "TicketDiagonal",
        "TICKET_HORIZONTAL": "TicketHorizontal",
        "TIME_AND_WEATHER": "TimeAndWeather",
        "TIMELINE": "Timeline",
        "TIME_PICKER": "TimePicker",
        "TIMER": "Timer",
        "TIMER10": "Timer10",
        "TIMER2": "Timer2",
        "TIMER3": "Timer3",
        "TIMER_OFF": "TimerOff",
        "TOGGLE_LEFT": "ToggleLeft",
        "TOGGLE_MULTIPLE": "ToggleMultiple",
        "TOGGLE_RIGHT": "ToggleRight",
        "TOILET": "Toilet",
        "TOOLBOX": "Toolbox",
        "TOOLTIP_QUOTE": "TooltipQuote",
        "TOOLTIP_QUOTE_OFF": "TooltipQuoteOff",
        "TOP_SPEED": "TopSpeed",
        "TRANSLATE": "Translate",
        "TRANSLATE_AUTO": "TranslateAuto",
        "TRANSLATE_OFF": "TranslateOff",
        "TRANSMISSION": "Transmission",
        "TRANSPARENCY_SQUARE": "TransparencySquare",
        "TRAY_ITEM_ADD": "TrayItemAdd",
        "TRAY_ITEM_REMOVE": "TrayItemRemove",
        "TREE_DECIDUOUS": "TreeDeciduous",
        "TREE_EVERGREEN": "TreeEvergreen",
        "TRIANGLE": "Triangle",
        "TRIANGLE_DOWN": "TriangleDown",
        "TRIANGLE_LEFT": "TriangleLeft",
        "TRIANGLE_RIGHT": "TriangleRight",
        "TRIANGLE_UP": "TriangleUp",
        "TROPHY": "Trophy",
        "TROPHY_LOCK": "TrophyLock",
        "TROPHY_OFF": "TrophyOff",
        "T_V": "TV",
        "T_V_ARROW_RIGHT": "TVArrowRight",
        "T_V_U_S_B": "TVUSB",
        "UMBRELLA": "Umbrella",
        "UNINSTALL_APP": "UninstallApp",
        "U_S_B_PLUG": "USBPlug",
        "USB_STICK": "UsbStick",
        "VAULT": "Vault",
        "VEHICLE_BICYCLE": "VehicleBicycle",
        "VEHICLE_BUS": "VehicleBus",
        "VEHICLE_CAB": "VehicleCab",
        "VEHICLE_CABLE_CAR": "VehicleCableCar",
        "VEHICLE_CAR": "VehicleCar",
        "VEHICLE_CAR_COLLISION": "VehicleCarCollision",
        "VEHICLE_CAR_PARKING": "VehicleCarParking",
        "VEHICLE_CAR_PROFILE": "VehicleCarProfile",
        "VEHICLE_CAR_PROFILE_L_T_R": "VehicleCarProfileLTR",
        "VEHICLE_CAR_PROFILE_L_T_R_CLOCK": "VehicleCarProfileLTRClock",
        "VEHICLE_CAR_PROFILE_R_T_L": "VehicleCarProfileRTL",
        "VEHICLE_MOTORCYCLE": "VehicleMotorcycle",
        "VEHICLE_R_V": "VehicleRV",
        "VEHICLE_SHIP": "VehicleShip",
        "VEHICLE_SUBWAY": "VehicleSubway",
        "VEHICLE_SUBWAY_CLOCK": "VehicleSubwayClock",
        "VEHICLE_TRACTOR": "VehicleTractor",
        "VEHICLE_TRAILER": "VehicleTrailer",
        "VEHICLE_TRAILER_ARROW_DOWN": "VehicleTrailerArrowDown",
        "VEHICLE_TRUCK": "VehicleTruck",
        "VEHICLE_TRUCK_BAG": "VehicleTruckBag",
        "VEHICLE_TRUCK_CHECKMARK": "VehicleTruckCheckmark",
        "VEHICLE_TRUCK_CUBE": "VehicleTruckCube",
        "VEHICLE_TRUCK_PROFILE": "VehicleTruckProfile",
        "VIDEO": "Video",
        "VIDEO360": "Video360",
        "VIDEO360_OFF": "Video360Off",
        "VIDEO_ADD": "VideoAdd",
        "VIDEO_BACKGROUND_EFFECT": "VideoBackgroundEffect",
        "VIDEO_BACKGROUND_EFFECT_HORIZONTAL": "VideoBackgroundEffectHorizontal",
        "VIDEO_BLUETOOTH": "VideoBluetooth",
        "VIDEO_CHAT": "VideoChat",
        "VIDEO_LINK": "VideoLink",
        "VIDEO_MULTIPLE": "VideoMultiple",
        "VIDEO_OFF": "VideoOff",
        "VIDEO_PERSON": "VideoPerson",
        "VIDEO_PERSON_CALL": "VideoPersonCall",
        "VIDEO_PERSON_CLOCK": "VideoPersonClock",
        "VIDEO_PERSON_OFF": "VideoPersonOff",
        "VIDEO_PERSON_PULSE": "VideoPersonPulse",
        "VIDEO_PERSON_SPARKLE": "VideoPersonSparkle",
        "VIDEO_PERSON_SPARKLE_OFF": "VideoPersonSparkleOff",
        "VIDEO_PERSON_STAR": "VideoPersonStar",
        "VIDEO_PERSON_STAR_OFF": "VideoPersonStarOff",
        "VIDEO_PLAY_PAUSE": "VideoPlayPause",
        "VIDEO_PROHIBITED": "VideoProhibited",
        "VIDEO_RECORDING": "VideoRecording",
        "VIDEO_SECURITY": "VideoSecurity",
        "VIDEO_SETTINGS": "VideoSettings",
        "VIDEO_SHORT": "VideoShort",
        "VIDEO_SHORT_MULTIPLE": "VideoShortMultiple",
        "VIDEO_SWITCH": "VideoSwitch",
        "VIDEO_SYNC": "VideoSync",
        "VIDEO_U_S_B": "VideoUSB",
        "VIEW_DESKTOP": "ViewDesktop",
        "VIEW_DESKTOP_MOBILE": "ViewDesktopMobile",
        "VIRTUAL_NETWORK": "VirtualNetwork",
        "VIRTUAL_NETWORK_TOOLBOX": "VirtualNetworkToolbox",
        "VOICEMAIL": "Voicemail",
        "VOICEMAIL_ARROW_BACK": "VoicemailArrowBack",
        "VOICEMAIL_ARROW_FORWARD": "VoicemailArrowForward",
        "VOICEMAIL_ARROW_SUBTRACT": "VoicemailArrowSubtract",
        "VOICEMAIL_SHIELD": "VoicemailShield",
        "VOICEMAIL_SUBTRACT": "VoicemailSubtract",
        "VOTE": "Vote",
        "WALKIE_TALKIE": "WalkieTalkie",
        "WALLET": "Wallet",
        "WALLET_CREDIT_CARD": "WalletCreditCard",
        "WALLPAPER": "Wallpaper",
        "WAND": "Wand",
        "WARNING": "Warning",
        "WARNING_LOCK_OPEN": "WarningLockOpen",
        "WARNING_SHIELD": "WarningShield",
        "WASHER": "Washer",
        "WATER": "Water",
        "WEATHER_BLOWING_SNOW": "WeatherBlowingSnow",
        "WEATHER_CLOUDY": "WeatherCloudy",
        "WEATHER_DRIZZLE": "WeatherDrizzle",
        "WEATHER_DUSTSTORM": "WeatherDuststorm",
        "WEATHER_FOG": "WeatherFog",
        "WEATHER_HAIL_DAY": "WeatherHailDay",
        "WEATHER_HAIL_NIGHT": "WeatherHailNight",
        "WEATHER_HAZE": "WeatherHaze",
        "WEATHER_MOON": "WeatherMoon",
        "WEATHER_MOON_OFF": "WeatherMoonOff",
        "WEATHER_PARTLY_CLOUDY_DAY": "WeatherPartlyCloudyDay",
        "WEATHER_PARTLY_CLOUDY_NIGHT": "WeatherPartlyCloudyNight",
        "WEATHER_RAIN": "WeatherRain",
        "WEATHER_RAIN_SHOWERS_DAY": "WeatherRainShowersDay",
        "WEATHER_RAIN_SHOWERS_NIGHT": "WeatherRainShowersNight",
        "WEATHER_RAIN_SNOW": "WeatherRainSnow",
        "WEATHER_SNOW": "WeatherSnow",
        "WEATHER_SNOWFLAKE": "WeatherSnowflake",
        "WEATHER_SNOW_SHOWER_DAY": "WeatherSnowShowerDay",
        "WEATHER_SNOW_SHOWER_NIGHT": "WeatherSnowShowerNight",
        "WEATHER_SQUALLS": "WeatherSqualls",
        "WEATHER_SUNNY": "WeatherSunny",
        "WEATHER_SUNNY_HIGH": "WeatherSunnyHigh",
        "WEATHER_SUNNY_LOW": "WeatherSunnyLow",
        "WEATHER_THUNDERSTORM": "WeatherThunderstorm",
        "WEB_ASSET": "WebAsset",
        "WHEELCHAIR_ACCESS": "WheelchairAccess",
        "WHITEBOARD": "Whiteboard",
        "WHITEBOARD_OFF": "WhiteboardOff",
        "WI_FI1": "WiFi1",
        "WI_FI2": "WiFi2",
        "WI_FI3": "WiFi3",
        "WI_FI4": "WiFi4",
        "WI_FI_LOCK": "WiFiLock",
        "WI_FI_OFF": "WiFiOff",
        "WI_FI_SETTINGS": "WiFiSettings",
        "WI_FI_WARNING": "WiFiWarning",
        "WINDOW": "Window",
        "WINDOW_AD": "WindowAd",
        "WINDOW_AD_OFF": "WindowAdOff",
        "WINDOW_AD_PERSON": "WindowAdPerson",
        "WINDOW_APPS": "WindowApps",
        "WINDOW_ARROW_UP": "WindowArrowUp",
        "WINDOW_BRUSH": "WindowBrush",
        "WINDOW_BULLET_LIST": "WindowBulletList",
        "WINDOW_BULLET_LIST_ADD": "WindowBulletListAdd",
        "WINDOW_COLUMN_ONE_FOURTH_LEFT": "WindowColumnOneFourthLeft",
        "WINDOW_CONSOLE": "WindowConsole",
        "WINDOW_DATABASE": "WindowDatabase",
        "WINDOW_DEV_EDIT": "WindowDevEdit",
        "WINDOW_DEV_TOOLS": "WindowDevTools",
        "WINDOW_EDIT": "WindowEdit",
        "WINDOW_FINGERPRINT": "WindowFingerprint",
        "WINDOW_HEADER_HORIZONTAL": "WindowHeaderHorizontal",
        "WINDOW_HEADER_HORIZONTAL_OFF": "WindowHeaderHorizontalOff",
        "WINDOW_HEADER_VERTICAL": "WindowHeaderVertical",
        "WINDOW_IN_PRIVATE": "WindowInPrivate",
        "WINDOW_IN_PRIVATE_ACCOUNT": "WindowInPrivateAccount",
        "WINDOW_LOCATION_TARGET": "WindowLocationTarget",
        "WINDOW_MULTIPLE": "WindowMultiple",
        "WINDOW_MULTIPLE_SWAP": "WindowMultipleSwap",
        "WINDOW_NEW": "WindowNew",
        "WINDOW_PLAY": "WindowPlay",
        "WINDOW_SETTINGS": "WindowSettings",
        "WINDOW_SHIELD": "WindowShield",
        "WINDOW_TEXT": "WindowText",
        "WINDOW_WRENCH": "WindowWrench",
        "WRENCH": "Wrench",
        "WRENCH_SCREWDRIVER": "WrenchScrewdriver",
        "WRENCH_SETTINGS": "WrenchSettings",
        "XBOX_CONSOLE": "XboxConsole",
        "XBOX_CONTROLLER": "XboxController",
        "XBOX_CONTROLLER_ERROR": "XboxControllerError",
        "XRAY": "Xray",
        "ZOOM_FIT": "ZoomFit",
        "ZOOM_IN": "ZoomIn",
        "ZOOM_OUT": "ZoomOut"    }
    
    // ==================== Icon Properties 图标属性 ====================
    readonly property string accessibility: "Accessibility"
    readonly property string accessibility_checkmark: "AccessibilityCheckmark"
    readonly property string accessibility_error: "AccessibilityError"
    readonly property string accessibility_more: "AccessibilityMore"
    readonly property string accessibility_question_mark: "AccessibilityQuestionMark"
    readonly property string access_time: "AccessTime"
    readonly property string add: "Add"
    readonly property string add_circle: "AddCircle"
    readonly property string add_square: "AddSquare"
    readonly property string add_square_multiple: "AddSquareMultiple"
    readonly property string add_starburst: "AddStarburst"
    readonly property string add_subtract_circle: "AddSubtractCircle"
    readonly property string agents: "Agents"
    readonly property string agents_add: "AgentsAdd"
    readonly property string airplane: "Airplane"
    readonly property string airplane_landing: "AirplaneLanding"
    readonly property string airplane_take_off: "AirplaneTakeOff"
    readonly property string album: "Album"
    readonly property string album_add: "AlbumAdd"
    readonly property string alert: "Alert"
    readonly property string alert_badge: "AlertBadge"
    readonly property string alert_off: "AlertOff"
    readonly property string alert_on: "AlertOn"
    readonly property string alert_snooze: "AlertSnooze"
    readonly property string alert_urgent: "AlertUrgent"
    readonly property string animal_cat: "AnimalCat"
    readonly property string animal_dog: "AnimalDog"
    readonly property string animal_paw_print: "AnimalPawPrint"
    readonly property string animal_rabbit: "AnimalRabbit"
    readonly property string animal_rabbit_off: "AnimalRabbitOff"
    readonly property string animal_turtle: "AnimalTurtle"
    readonly property string app_folder: "AppFolder"
    readonly property string app_generic: "AppGeneric"
    readonly property string app_recent: "AppRecent"
    readonly property string approvals_app: "ApprovalsApp"
    readonly property string apps: "Apps"
    readonly property string apps_add_in: "AppsAddIn"
    readonly property string apps_add_in_off: "AppsAddInOff"
    readonly property string apps_list: "AppsList"
    readonly property string apps_list_detail: "AppsListDetail"
    readonly property string apps_settings: "AppsSettings"
    readonly property string apps_shield: "AppsShield"
    readonly property string app_store: "AppStore"
    readonly property string app_title: "AppTitle"
    readonly property string archive: "Archive"
    readonly property string archive_arrow_back: "ArchiveArrowBack"
    readonly property string archive_clock: "ArchiveClock"
    readonly property string archive_multiple: "ArchiveMultiple"
    readonly property string archive_settings: "ArchiveSettings"
    readonly property string arrow_autofit_content: "ArrowAutofitContent"
    readonly property string arrow_autofit_down: "ArrowAutofitDown"
    readonly property string arrow_autofit_height: "ArrowAutofitHeight"
    readonly property string arrow_autofit_height_dotted: "ArrowAutofitHeightDotted"
    readonly property string arrow_autofit_height_in: "ArrowAutofitHeightIn"
    readonly property string arrow_autofit_up: "ArrowAutofitUp"
    readonly property string arrow_autofit_width: "ArrowAutofitWidth"
    readonly property string arrow_autofit_width_dotted: "ArrowAutofitWidthDotted"
    readonly property string arrow_between_down: "ArrowBetweenDown"
    readonly property string arrow_between_up: "ArrowBetweenUp"
    readonly property string arrow_bidirectional_left_right: "ArrowBidirectionalLeftRight"
    readonly property string arrow_bidirectional_up_down: "ArrowBidirectionalUpDown"
    readonly property string arrow_bounce: "ArrowBounce"
    readonly property string arrow_circle_down: "ArrowCircleDown"
    readonly property string arrow_circle_down_double: "ArrowCircleDownDouble"
    readonly property string arrow_circle_down_right: "ArrowCircleDownRight"
    readonly property string arrow_circle_down_split: "ArrowCircleDownSplit"
    readonly property string arrow_circle_down_up: "ArrowCircleDownUp"
    readonly property string arrow_circle_left: "ArrowCircleLeft"
    readonly property string arrow_circle_right: "ArrowCircleRight"
    readonly property string arrow_circle_up: "ArrowCircleUp"
    readonly property string arrow_circle_up_left: "ArrowCircleUpLeft"
    readonly property string arrow_circle_up_right: "ArrowCircleUpRight"
    readonly property string arrow_circle_up_sparkle: "ArrowCircleUpSparkle"
    readonly property string arrow_clockwise: "ArrowClockwise"
    readonly property string arrow_clockwise_dashes: "ArrowClockwiseDashes"
    readonly property string arrow_clockwise_dashes_settings: "ArrowClockwiseDashesSettings"
    readonly property string arrow_collapse_all: "ArrowCollapseAll"
    readonly property string arrow_counterclockwise: "ArrowCounterclockwise"
    readonly property string arrow_counterclockwise_dashes: "ArrowCounterclockwiseDashes"
    readonly property string arrow_counterclockwise_info: "ArrowCounterclockwiseInfo"
    readonly property string arrow_curve_down_left: "ArrowCurveDownLeft"
    readonly property string arrow_curve_down_right: "ArrowCurveDownRight"
    readonly property string arrow_curve_up_left: "ArrowCurveUpLeft"
    readonly property string arrow_curve_up_right: "ArrowCurveUpRight"
    readonly property string arrow_down: "ArrowDown"
    readonly property string arrow_down_exclamation: "ArrowDownExclamation"
    readonly property string arrow_down_left: "ArrowDownLeft"
    readonly property string arrow_download: "ArrowDownload"
    readonly property string arrow_download_off: "ArrowDownloadOff"
    readonly property string arrow_down_right: "ArrowDownRight"
    readonly property string arrow_eject: "ArrowEject"
    readonly property string arrow_enter: "ArrowEnter"
    readonly property string arrow_enter_left: "ArrowEnterLeft"
    readonly property string arrow_enter_up: "ArrowEnterUp"
    readonly property string arrow_exit: "ArrowExit"
    readonly property string arrow_expand: "ArrowExpand"
    readonly property string arrow_expand_all: "ArrowExpandAll"
    readonly property string arrow_export: "ArrowExport"
    readonly property string arrow_export_l_t_r: "ArrowExportLTR"
    readonly property string arrow_export_r_t_l: "ArrowExportRTL"
    readonly property string arrow_export_up: "ArrowExportUp"
    readonly property string arrow_fit: "ArrowFit"
    readonly property string arrow_fit_in: "ArrowFitIn"
    readonly property string arrow_flow_diagonal_up_right: "ArrowFlowDiagonalUpRight"
    readonly property string arrow_flow_up_right: "ArrowFlowUpRight"
    readonly property string arrow_flow_up_right_rectangle_multiple: "ArrowFlowUpRightRectangleMultiple"
    readonly property string arrow_forward: "ArrowForward"
    readonly property string arrow_forward_down_lightning: "ArrowForwardDownLightning"
    readonly property string arrow_forward_down_person: "ArrowForwardDownPerson"
    readonly property string arrow_hook_down_left: "ArrowHookDownLeft"
    readonly property string arrow_hook_down_right: "ArrowHookDownRight"
    readonly property string arrow_hook_up_left: "ArrowHookUpLeft"
    readonly property string arrow_hook_up_right: "ArrowHookUpRight"
    readonly property string arrow_import: "ArrowImport"
    readonly property string arrow_join: "ArrowJoin"
    readonly property string arrow_left: "ArrowLeft"
    readonly property string arrow_maximize: "ArrowMaximize"
    readonly property string arrow_maximize_top_left_bottom_right: "ArrowMaximizeTopLeftBottomRight"
    readonly property string arrow_maximize_vertical: "ArrowMaximizeVertical"
    readonly property string arrow_minimize: "ArrowMinimize"
    readonly property string arrow_minimize_top_left_bottom_right: "ArrowMinimizeTopLeftBottomRight"
    readonly property string arrow_minimize_vertical: "ArrowMinimizeVertical"
    readonly property string arrow_move: "ArrowMove"
    readonly property string arrow_move_inward: "ArrowMoveInward"
    readonly property string arrow_next: "ArrowNext"
    readonly property string arrow_outline_down_left: "ArrowOutlineDownLeft"
    readonly property string arrow_outline_up_right: "ArrowOutlineUpRight"
    readonly property string arrow_paragraph: "ArrowParagraph"
    readonly property string arrow_previous: "ArrowPrevious"
    readonly property string arrow_redo: "ArrowRedo"
    readonly property string arrow_redo_temp_l_t_r: "ArrowRedoTempLTR"
    readonly property string arrow_redo_temp_r_t_l: "ArrowRedoTempRTL"
    readonly property string arrow_repeat1: "ArrowRepeat1"
    readonly property string arrow_repeat_all: "ArrowRepeatAll"
    readonly property string arrow_repeat_all_off: "ArrowRepeatAllOff"
    readonly property string arrow_reply: "ArrowReply"
    readonly property string arrow_reply_all: "ArrowReplyAll"
    readonly property string arrow_reply_down: "ArrowReplyDown"
    readonly property string arrow_reset: "ArrowReset"
    readonly property string arrow_right: "ArrowRight"
    readonly property string arrow_rotate_clockwise: "ArrowRotateClockwise"
    readonly property string arrow_rotate_counterclockwise: "ArrowRotateCounterclockwise"
    readonly property string arrow_routing: "ArrowRouting"
    readonly property string arrow_routing_rectangle_multiple: "ArrowRoutingRectangleMultiple"
    readonly property string arrows_bidirectional: "ArrowsBidirectional"
    readonly property string arrow_shuffle: "ArrowShuffle"
    readonly property string arrow_shuffle_off: "ArrowShuffleOff"
    readonly property string arrow_sort: "ArrowSort"
    readonly property string arrow_sort_down: "ArrowSortDown"
    readonly property string arrow_sort_down_lines: "ArrowSortDownLines"
    readonly property string arrow_sort_up: "ArrowSortUp"
    readonly property string arrow_sort_up_lines: "ArrowSortUpLines"
    readonly property string arrow_split: "ArrowSplit"
    readonly property string arrow_sprint: "ArrowSprint"
    readonly property string arrow_square_down: "ArrowSquareDown"
    readonly property string arrow_square_up_right: "ArrowSquareUpRight"
    readonly property string arrow_step_back: "ArrowStepBack"
    readonly property string arrow_step_in: "ArrowStepIn"
    readonly property string arrow_step_in_diagonal_down_left: "ArrowStepInDiagonalDownLeft"
    readonly property string arrow_step_in_left: "ArrowStepInLeft"
    readonly property string arrow_step_in_right: "ArrowStepInRight"
    readonly property string arrow_step_out: "ArrowStepOut"
    readonly property string arrow_step_over: "ArrowStepOver"
    readonly property string arrow_swap: "ArrowSwap"
    readonly property string arrow_sync: "ArrowSync"
    readonly property string arrow_sync_checkmark: "ArrowSyncCheckmark"
    readonly property string arrow_sync_circle: "ArrowSyncCircle"
    readonly property string arrow_sync_dismiss: "ArrowSyncDismiss"
    readonly property string arrow_sync_off: "ArrowSyncOff"
    readonly property string arrow_trending: "ArrowTrending"
    readonly property string arrow_trending_checkmark: "ArrowTrendingCheckmark"
    readonly property string arrow_trending_down: "ArrowTrendingDown"
    readonly property string arrow_trending_lines: "ArrowTrendingLines"
    readonly property string arrow_trending_settings: "ArrowTrendingSettings"
    readonly property string arrow_trending_sparkle: "ArrowTrendingSparkle"
    readonly property string arrow_trending_text: "ArrowTrendingText"
    readonly property string arrow_trending_wrench: "ArrowTrendingWrench"
    readonly property string arrow_turn_bidirectional_down_right: "ArrowTurnBidirectionalDownRight"
    readonly property string arrow_turn_down_left: "ArrowTurnDownLeft"
    readonly property string arrow_turn_down_right: "ArrowTurnDownRight"
    readonly property string arrow_turn_down_up: "ArrowTurnDownUp"
    readonly property string arrow_turn_left_down: "ArrowTurnLeftDown"
    readonly property string arrow_turn_left_right: "ArrowTurnLeftRight"
    readonly property string arrow_turn_left_up: "ArrowTurnLeftUp"
    readonly property string arrow_turn_right: "ArrowTurnRight"
    readonly property string arrow_turn_right_down: "ArrowTurnRightDown"
    readonly property string arrow_turn_right_left: "ArrowTurnRightLeft"
    readonly property string arrow_turn_right_up: "ArrowTurnRightUp"
    readonly property string arrow_turn_up_down: "ArrowTurnUpDown"
    readonly property string arrow_turn_up_left: "ArrowTurnUpLeft"
    readonly property string arrow_undo: "ArrowUndo"
    readonly property string arrow_undo_temp_l_t_r: "ArrowUndoTempLTR"
    readonly property string arrow_undo_temp_r_t_l: "ArrowUndoTempRTL"
    readonly property string arrow_up: "ArrowUp"
    readonly property string arrow_up_exclamation: "ArrowUpExclamation"
    readonly property string arrow_up_left: "ArrowUpLeft"
    readonly property string arrow_upload: "ArrowUpload"
    readonly property string arrow_up_right: "ArrowUpRight"
    readonly property string arrow_up_right_dashes: "ArrowUpRightDashes"
    readonly property string arrow_up_square_settings: "ArrowUpSquareSettings"
    readonly property string arrow_wrap: "ArrowWrap"
    readonly property string arrow_wrap_off: "ArrowWrapOff"
    readonly property string arrow_wrap_up_to_down: "ArrowWrapUpToDown"
    readonly property string attach: "Attach"
    readonly property string attach_arrow_right: "AttachArrowRight"
    readonly property string attach_text: "AttachText"
    readonly property string autocorrect: "Autocorrect"
    readonly property string auto_fit_height: "AutoFitHeight"
    readonly property string auto_fit_width: "AutoFitWidth"
    readonly property string auto_sum: "AutoSum"
    readonly property string backpack: "Backpack"
    readonly property string backpack_add: "BackpackAdd"
    readonly property string backspace: "Backspace"
    readonly property string badge: "Badge"
    readonly property string balcony: "Balcony"
    readonly property string balloon: "Balloon"
    readonly property string barcode_scanner: "BarcodeScanner"
    readonly property string barcode_scanner_add: "BarcodeScannerAdd"
    readonly property string barcode_scanner_dismiss: "BarcodeScannerDismiss"
    readonly property string battery0: "Battery0"
    readonly property string battery1: "Battery1"
    readonly property string battery10: "Battery10"
    readonly property string battery2: "Battery2"
    readonly property string battery3: "Battery3"
    readonly property string battery4: "Battery4"
    readonly property string battery5: "Battery5"
    readonly property string battery6: "Battery6"
    readonly property string battery7: "Battery7"
    readonly property string battery8: "Battery8"
    readonly property string battery9: "Battery9"
    readonly property string battery_charge: "BatteryCharge"
    readonly property string battery_charge0: "BatteryCharge0"
    readonly property string battery_charge1: "BatteryCharge1"
    readonly property string battery_charge10: "BatteryCharge10"
    readonly property string battery_charge2: "BatteryCharge2"
    readonly property string battery_charge3: "BatteryCharge3"
    readonly property string battery_charge4: "BatteryCharge4"
    readonly property string battery_charge5: "BatteryCharge5"
    readonly property string battery_charge6: "BatteryCharge6"
    readonly property string battery_charge7: "BatteryCharge7"
    readonly property string battery_charge8: "BatteryCharge8"
    readonly property string battery_charge9: "BatteryCharge9"
    readonly property string battery_checkmark: "BatteryCheckmark"
    readonly property string battery_saver: "BatterySaver"
    readonly property string battery_warning: "BatteryWarning"
    readonly property string beach: "Beach"
    readonly property string beaker: "Beaker"
    readonly property string beaker_add: "BeakerAdd"
    readonly property string beaker_dismiss: "BeakerDismiss"
    readonly property string beaker_edit: "BeakerEdit"
    readonly property string beaker_empty: "BeakerEmpty"
    readonly property string beaker_off: "BeakerOff"
    readonly property string beaker_settings: "BeakerSettings"
    readonly property string bed: "Bed"
    readonly property string bench: "Bench"
    readonly property string bezier_curve_square: "BezierCurveSquare"
    readonly property string binder_triangle: "BinderTriangle"
    readonly property string bin_full: "BinFull"
    readonly property string bin_recycle: "BinRecycle"
    readonly property string bin_recycle_full: "BinRecycleFull"
    readonly property string bluetooth: "Bluetooth"
    readonly property string bluetooth_connected: "BluetoothConnected"
    readonly property string bluetooth_disabled: "BluetoothDisabled"
    readonly property string bluetooth_searching: "BluetoothSearching"
    readonly property string blur: "Blur"
    readonly property string board: "Board"
    readonly property string board_games: "BoardGames"
    readonly property string board_heart: "BoardHeart"
    readonly property string board_split: "BoardSplit"
    readonly property string book: "Book"
    readonly property string book_add: "BookAdd"
    readonly property string book_arrow_clockwise: "BookArrowClockwise"
    readonly property string book_clock: "BookClock"
    readonly property string book_coins: "BookCoins"
    readonly property string book_compass: "BookCompass"
    readonly property string book_contacts: "BookContacts"
    readonly property string book_database: "BookDatabase"
    readonly property string book_dismiss: "BookDismiss"
    readonly property string book_exclamation_mark: "BookExclamationMark"
    readonly property string book_globe: "BookGlobe"
    readonly property string book_information: "BookInformation"
    readonly property string book_letter: "BookLetter"
    readonly property string bookmark: "Bookmark"
    readonly property string bookmark_add: "BookmarkAdd"
    readonly property string bookmark_multiple: "BookmarkMultiple"
    readonly property string bookmark_off: "BookmarkOff"
    readonly property string bookmark_search: "BookmarkSearch"
    readonly property string book_number: "BookNumber"
    readonly property string book_open: "BookOpen"
    readonly property string book_open_globe: "BookOpenGlobe"
    readonly property string book_open_lightbulb: "BookOpenLightbulb"
    readonly property string book_open_microphone: "BookOpenMicrophone"
    readonly property string book_pulse: "BookPulse"
    readonly property string book_question_mark: "BookQuestionMark"
    readonly property string book_question_mark_r_t_l: "BookQuestionMarkRTL"
    readonly property string book_search: "BookSearch"
    readonly property string book_star: "BookStar"
    readonly property string book_template: "BookTemplate"
    readonly property string book_theta: "BookTheta"
    readonly property string book_toolbox: "BookToolbox"
    readonly property string bot: "Bot"
    readonly property string bot_add: "BotAdd"
    readonly property string bot_sparkle: "BotSparkle"
    readonly property string bowl_chopsticks: "BowlChopsticks"
    readonly property string bowl_salad: "BowlSalad"
    readonly property string bow_tie: "BowTie"
    readonly property string box: "Box"
    readonly property string box_arrow_left: "BoxArrowLeft"
    readonly property string box_arrow_up: "BoxArrowUp"
    readonly property string box_checkmark: "BoxCheckmark"
    readonly property string box_dismiss: "BoxDismiss"
    readonly property string box_edit: "BoxEdit"
    readonly property string box_multiple: "BoxMultiple"
    readonly property string box_multiple_arrow_left: "BoxMultipleArrowLeft"
    readonly property string box_multiple_arrow_right: "BoxMultipleArrowRight"
    readonly property string box_multiple_checkmark: "BoxMultipleCheckmark"
    readonly property string box_multiple_search: "BoxMultipleSearch"
    readonly property string box_search: "BoxSearch"
    readonly property string box_toolbox: "BoxToolbox"
    readonly property string braces: "Braces"
    readonly property string braces_checkmark: "BracesCheckmark"
    readonly property string braces_dismiss: "BracesDismiss"
    readonly property string braces_variable: "BracesVariable"
    readonly property string brain: "Brain"
    readonly property string brain_circuit: "BrainCircuit"
    readonly property string brain_sparkle: "BrainSparkle"
    readonly property string branch: "Branch"
    readonly property string branch_compare: "BranchCompare"
    readonly property string branch_fork: "BranchFork"
    readonly property string branch_fork_hint: "BranchForkHint"
    readonly property string branch_fork_link: "BranchForkLink"
    readonly property string branch_request: "BranchRequest"
    readonly property string branch_request_closed: "BranchRequestClosed"
    readonly property string branch_request_draft: "BranchRequestDraft"
    readonly property string breakout_room: "BreakoutRoom"
    readonly property string briefcase: "Briefcase"
    readonly property string briefcase_medical: "BriefcaseMedical"
    readonly property string briefcase_off: "BriefcaseOff"
    readonly property string briefcase_person: "BriefcasePerson"
    readonly property string briefcase_search: "BriefcaseSearch"
    readonly property string brightness_high: "BrightnessHigh"
    readonly property string brightness_low: "BrightnessLow"
    readonly property string broad_activity_feed: "BroadActivityFeed"
    readonly property string broom: "Broom"
    readonly property string broom_sparkle: "BroomSparkle"
    readonly property string bubble_multiple: "BubbleMultiple"
    readonly property string bug: "Bug"
    readonly property string bug_arrow_counterclockwise: "BugArrowCounterclockwise"
    readonly property string bug_prohibited: "BugProhibited"
    readonly property string building: "Building"
    readonly property string building_bank: "BuildingBank"
    readonly property string building_bank_link: "BuildingBankLink"
    readonly property string building_bank_toolbox: "BuildingBankToolbox"
    readonly property string building_checkmark: "BuildingCheckmark"
    readonly property string building_cloud: "BuildingCloud"
    readonly property string building_desktop: "BuildingDesktop"
    readonly property string building_factory: "BuildingFactory"
    readonly property string building_government: "BuildingGovernment"
    readonly property string building_government_search: "BuildingGovernmentSearch"
    readonly property string building_home: "BuildingHome"
    readonly property string building_lighthouse: "BuildingLighthouse"
    readonly property string building_mosque: "BuildingMosque"
    readonly property string building_multiple: "BuildingMultiple"
    readonly property string building_people: "BuildingPeople"
    readonly property string building_retail: "BuildingRetail"
    readonly property string building_retail_money: "BuildingRetailMoney"
    readonly property string building_retail_more: "BuildingRetailMore"
    readonly property string building_retail_shield: "BuildingRetailShield"
    readonly property string building_retail_toolbox: "BuildingRetailToolbox"
    readonly property string building_shop: "BuildingShop"
    readonly property string building_skyscraper: "BuildingSkyscraper"
    readonly property string building_swap: "BuildingSwap"
    readonly property string building_townhouse: "BuildingTownhouse"
    readonly property string building_yurt: "BuildingYurt"
    readonly property string button: "Button"
    readonly property string calculator: "Calculator"
    readonly property string calculator_arrow_clockwise: "CalculatorArrowClockwise"
    readonly property string calculator_multiple: "CalculatorMultiple"
    readonly property string calendar: "Calendar"
    readonly property string call: "Call"
    readonly property string call_add: "CallAdd"
    readonly property string call_checkmark: "CallCheckmark"
    readonly property string call_connecting: "CallConnecting"
    readonly property string call_dismiss: "CallDismiss"
    readonly property string call_end: "CallEnd"
    readonly property string call_exclamation: "CallExclamation"
    readonly property string call_forward: "CallForward"
    readonly property string calligraphy_pen: "CalligraphyPen"
    readonly property string calligraphy_pen_checkmark: "CalligraphyPenCheckmark"
    readonly property string calligraphy_pen_error: "CalligraphyPenError"
    readonly property string calligraphy_pen_question_mark: "CalligraphyPenQuestionMark"
    readonly property string call_inbound: "CallInbound"
    readonly property string call_missed: "CallMissed"
    readonly property string call_outbound: "CallOutbound"
    readonly property string call_park: "CallPark"
    readonly property string call_pause: "CallPause"
    readonly property string call_prohibited: "CallProhibited"
    readonly property string call_rectangle_landscape: "CallRectangleLandscape"
    readonly property string call_square: "CallSquare"
    readonly property string call_transfer: "CallTransfer"
    readonly property string call_warning: "CallWarning"
    readonly property string camera: "Camera"
    readonly property string camera_add: "CameraAdd"
    readonly property string camera_arrow_up: "CameraArrowUp"
    readonly property string camera_dome: "CameraDome"
    readonly property string camera_edit: "CameraEdit"
    readonly property string camera_off: "CameraOff"
    readonly property string camera_sparkles: "CameraSparkles"
    readonly property string camera_switch: "CameraSwitch"
    readonly property string card_u_i: "CardUI"
    readonly property string card_u_i_portrait_flip: "CardUIPortraitFlip"
    readonly property string caret_down: "CaretDown"
    readonly property string caret_down_right: "CaretDownRight"
    readonly property string caret_left: "CaretLeft"
    readonly property string caret_right: "CaretRight"
    readonly property string caret_up: "CaretUp"
    readonly property string cart: "Cart"
    readonly property string cast: "Cast"
    readonly property string cast_multiple: "CastMultiple"
    readonly property string catch_up: "CatchUp"
    readonly property string c_d: "CD"
    readonly property string cellular3_g: "Cellular3G"
    readonly property string cellular4_g: "Cellular4G"
    readonly property string cellular5_g: "Cellular5G"
    readonly property string cellular_data1: "CellularData1"
    readonly property string cellular_data2: "CellularData2"
    readonly property string cellular_data3: "CellularData3"
    readonly property string cellular_data4: "CellularData4"
    readonly property string cellular_data5: "CellularData5"
    readonly property string cellular_off: "CellularOff"
    readonly property string cellular_warning: "CellularWarning"
    readonly property string center_horizontal: "CenterHorizontal"
    readonly property string center_vertical: "CenterVertical"
    readonly property string certificate: "Certificate"
    readonly property string channel: "Channel"
    readonly property string channel_add: "ChannelAdd"
    readonly property string channel_alert: "ChannelAlert"
    readonly property string channel_arrow_left: "ChannelArrowLeft"
    readonly property string channel_dismiss: "ChannelDismiss"
    readonly property string channel_share: "ChannelShare"
    readonly property string channel_subtract: "ChannelSubtract"
    readonly property string chart_multiple: "ChartMultiple"
    readonly property string chart_person: "ChartPerson"
    readonly property string chat: "Chat"
    readonly property string chat_add: "ChatAdd"
    readonly property string chat_arrow_back: "ChatArrowBack"
    readonly property string chat_arrow_back_down: "ChatArrowBackDown"
    readonly property string chat_arrow_double_back: "ChatArrowDoubleBack"
    readonly property string chat_bubbles_question: "ChatBubblesQuestion"
    readonly property string chat_cursor: "ChatCursor"
    readonly property string chat_dismiss: "ChatDismiss"
    readonly property string chat_empty: "ChatEmpty"
    readonly property string chat_help: "ChatHelp"
    readonly property string chat_hint_half: "ChatHintHalf"
    readonly property string chat_history: "ChatHistory"
    readonly property string chat_lock: "ChatLock"
    readonly property string chat_mail: "ChatMail"
    readonly property string chat_multiple: "ChatMultiple"
    readonly property string chat_multiple_checkmark: "ChatMultipleCheckmark"
    readonly property string chat_multiple_heart: "ChatMultipleHeart"
    readonly property string chat_multiple_minus: "ChatMultipleMinus"
    readonly property string chat_off: "ChatOff"
    readonly property string chat_settings: "ChatSettings"
    readonly property string chat_sparkle: "ChatSparkle"
    readonly property string chat_video: "ChatVideo"
    readonly property string chat_warning: "ChatWarning"
    readonly property string check: "Check"
    readonly property string checkbox1: "Checkbox1"
    readonly property string checkbox2: "Checkbox2"
    readonly property string checkbox_arrow_right: "CheckboxArrowRight"
    readonly property string checkbox_checked: "CheckboxChecked"
    readonly property string checkbox_checked_sync: "CheckboxCheckedSync"
    readonly property string checkbox_indeterminate: "CheckboxIndeterminate"
    readonly property string checkbox_person: "CheckboxPerson"
    readonly property string checkbox_unchecked: "CheckboxUnchecked"
    readonly property string checkbox_warning: "CheckboxWarning"
    readonly property string checkmark: "Checkmark"
    readonly property string checkmark_circle: "CheckmarkCircle"
    readonly property string checkmark_circle_hint: "CheckmarkCircleHint"
    readonly property string checkmark_circle_square: "CheckmarkCircleSquare"
    readonly property string checkmark_circle_warning: "CheckmarkCircleWarning"
    readonly property string checkmark_lock: "CheckmarkLock"
    readonly property string checkmark_note: "CheckmarkNote"
    readonly property string checkmark_square: "CheckmarkSquare"
    readonly property string checkmark_starburst: "CheckmarkStarburst"
    readonly property string checkmark_underline_circle: "CheckmarkUnderlineCircle"
    readonly property string chess: "Chess"
    readonly property string chevron_circle_down: "ChevronCircleDown"
    readonly property string chevron_circle_left: "ChevronCircleLeft"
    readonly property string chevron_circle_right: "ChevronCircleRight"
    readonly property string chevron_circle_up: "ChevronCircleUp"
    readonly property string chevron_double_down: "ChevronDoubleDown"
    readonly property string chevron_double_left: "ChevronDoubleLeft"
    readonly property string chevron_double_right: "ChevronDoubleRight"
    readonly property string chevron_double_up: "ChevronDoubleUp"
    readonly property string chevron_down: "ChevronDown"
    readonly property string chevron_down_up: "ChevronDownUp"
    readonly property string chevron_left: "ChevronLeft"
    readonly property string chevron_right: "ChevronRight"
    readonly property string chevron_up: "ChevronUp"
    readonly property string chevron_up_down: "ChevronUpDown"
    readonly property string circle: "Circle"
    readonly property string circle_edit: "CircleEdit"
    readonly property string circle_eraser: "CircleEraser"
    readonly property string circle_half_fill: "CircleHalfFill"
    readonly property string circle_highlight: "CircleHighlight"
    readonly property string circle_hint: "CircleHint"
    readonly property string circle_hint_cursor: "CircleHintCursor"
    readonly property string circle_hint_dismiss: "CircleHintDismiss"
    readonly property string circle_hint_half_vertical: "CircleHintHalfVertical"
    readonly property string circle_image: "CircleImage"
    readonly property string circle_line: "CircleLine"
    readonly property string circle_multiple_concentric: "CircleMultipleConcentric"
    readonly property string circle_multiple_hint_checkmark: "CircleMultipleHintCheckmark"
    readonly property string circle_multiple_subtract_checkmark: "CircleMultipleSubtractCheckmark"
    readonly property string circle_off: "CircleOff"
    readonly property string circle_shadow: "CircleShadow"
    readonly property string circle_small: "CircleSmall"
    readonly property string circle_sparkle: "CircleSparkle"
    readonly property string city: "City"
    readonly property string icon_class: "Class"
    readonly property string classification: "Classification"
    readonly property string clear_formatting: "ClearFormatting"
    readonly property string clipboard: "Clipboard"
    readonly property string clock: "Clock"
    readonly property string clock_alarm: "ClockAlarm"
    readonly property string clock_arrow_download: "ClockArrowDownload"
    readonly property string clock_bill: "ClockBill"
    readonly property string clock_dismiss: "ClockDismiss"
    readonly property string clock_lock: "ClockLock"
    readonly property string clock_pause: "ClockPause"
    readonly property string clock_sparkle: "ClockSparkle"
    readonly property string clock_toolbox: "ClockToolbox"
    readonly property string clock_warning: "ClockWarning"
    readonly property string closed_caption: "ClosedCaption"
    readonly property string closed_caption_off: "ClosedCaptionOff"
    readonly property string clothes_hanger: "ClothesHanger"
    readonly property string cloud: "Cloud"
    readonly property string cloud_add: "CloudAdd"
    readonly property string cloud_archive: "CloudArchive"
    readonly property string cloud_arrow_down: "CloudArrowDown"
    readonly property string cloud_arrow_right: "CloudArrowRight"
    readonly property string cloud_arrow_up: "CloudArrowUp"
    readonly property string cloud_beaker: "CloudBeaker"
    readonly property string cloud_bidirectional: "CloudBidirectional"
    readonly property string cloud_checkmark: "CloudCheckmark"
    readonly property string cloud_cube: "CloudCube"
    readonly property string cloud_database: "CloudDatabase"
    readonly property string cloud_desktop: "CloudDesktop"
    readonly property string cloud_dismiss: "CloudDismiss"
    readonly property string cloud_edit: "CloudEdit"
    readonly property string cloud_error: "CloudError"
    readonly property string cloud_flow: "CloudFlow"
    readonly property string cloud_link: "CloudLink"
    readonly property string cloud_off: "CloudOff"
    readonly property string cloud_swap: "CloudSwap"
    readonly property string cloud_sync: "CloudSync"
    readonly property string cloud_words: "CloudWords"
    readonly property string clover: "Clover"
    readonly property string code: "Code"
    readonly property string code_block: "CodeBlock"
    readonly property string code_block_edit: "CodeBlockEdit"
    readonly property string code_circle: "CodeCircle"
    readonly property string code_c_s: "CodeCS"
    readonly property string code_c_s_rectangle: "CodeCSRectangle"
    readonly property string code_f_s: "CodeFS"
    readonly property string code_f_s_rectangle: "CodeFSRectangle"
    readonly property string code_j_s: "CodeJS"
    readonly property string code_j_s_rectangle: "CodeJSRectangle"
    readonly property string code_p_y: "CodePY"
    readonly property string code_p_y_rectangle: "CodePYRectangle"
    readonly property string code_r_b: "CodeRB"
    readonly property string code_r_b_rectangle: "CodeRBRectangle"
    readonly property string code_text: "CodeText"
    readonly property string code_text_edit: "CodeTextEdit"
    readonly property string code_text_off: "CodeTextOff"
    readonly property string code_t_s: "CodeTS"
    readonly property string code_t_s_rectangle: "CodeTSRectangle"
    readonly property string code_v_b: "CodeVB"
    readonly property string code_v_b_rectangle: "CodeVBRectangle"
    readonly property string coin_multiple: "CoinMultiple"
    readonly property string coin_stack: "CoinStack"
    readonly property string collections: "Collections"
    readonly property string collections_add: "CollectionsAdd"
    readonly property string collections_empty: "CollectionsEmpty"
    readonly property string color: "Color"
    readonly property string color_background: "ColorBackground"
    readonly property string color_background_accent: "ColorBackgroundAccent"
    readonly property string color_fill: "ColorFill"
    readonly property string color_fill_accent: "ColorFillAccent"
    readonly property string color_line: "ColorLine"
    readonly property string color_line_accent: "ColorLineAccent"
    readonly property string column: "Column"
    readonly property string column_arrow_right: "ColumnArrowRight"
    readonly property string column_double_compare: "ColumnDoubleCompare"
    readonly property string column_edit: "ColumnEdit"
    readonly property string column_single: "ColumnSingle"
    readonly property string column_single_compare: "ColumnSingleCompare"
    readonly property string column_triple: "ColumnTriple"
    readonly property string column_triple_edit: "ColumnTripleEdit"
    readonly property string comma: "Comma"
    readonly property string comment: "Comment"
    readonly property string comment_add: "CommentAdd"
    readonly property string comment_arrow_left: "CommentArrowLeft"
    readonly property string comment_arrow_left_temp_l_t_r: "CommentArrowLeftTempLTR"
    readonly property string comment_arrow_left_temp_r_t_l: "CommentArrowLeftTempRTL"
    readonly property string comment_arrow_right: "CommentArrowRight"
    readonly property string comment_arrow_right_temp_l_t_r: "CommentArrowRightTempLTR"
    readonly property string comment_arrow_right_temp_r_t_l: "CommentArrowRightTempRTL"
    readonly property string comment_badge: "CommentBadge"
    readonly property string comment_checkmark: "CommentCheckmark"
    readonly property string comment_dismiss: "CommentDismiss"
    readonly property string comment_edit: "CommentEdit"
    readonly property string comment_error: "CommentError"
    readonly property string comment_lightning: "CommentLightning"
    readonly property string comment_link: "CommentLink"
    readonly property string comment_mention: "CommentMention"
    readonly property string comment_multiple: "CommentMultiple"
    readonly property string comment_multiple_checkmark: "CommentMultipleCheckmark"
    readonly property string comment_multiple_link: "CommentMultipleLink"
    readonly property string comment_multiple_mention: "CommentMultipleMention"
    readonly property string comment_note: "CommentNote"
    readonly property string comment_off: "CommentOff"
    readonly property string comment_quote: "CommentQuote"
    readonly property string comment_text: "CommentText"
    readonly property string communication: "Communication"
    readonly property string communication_person: "CommunicationPerson"
    readonly property string communication_shield: "CommunicationShield"
    readonly property string compass_northwest: "CompassNorthwest"
    readonly property string compass_true_north: "CompassTrueNorth"
    readonly property string component2_double_tap_swipe_down: "Component2DoubleTapSwipeDown"
    readonly property string component2_double_tap_swipe_up: "Component2DoubleTapSwipeUp"
    readonly property string compose: "Compose"
    readonly property string cone: "Cone"
    readonly property string conference_room: "ConferenceRoom"
    readonly property string connected: "Connected"
    readonly property string connector: "Connector"
    readonly property string contact_card: "ContactCard"
    readonly property string contact_card_generic: "ContactCardGeneric"
    readonly property string contact_card_group: "ContactCardGroup"
    readonly property string contact_card_link: "ContactCardLink"
    readonly property string contact_card_ribbon: "ContactCardRibbon"
    readonly property string content_settings: "ContentSettings"
    readonly property string content_view: "ContentView"
    readonly property string content_view_gallery: "ContentViewGallery"
    readonly property string content_view_gallery_lightning: "ContentViewGalleryLightning"
    readonly property string contract_down_left: "ContractDownLeft"
    readonly property string contract_up_right: "ContractUpRight"
    readonly property string control_button: "ControlButton"
    readonly property string convert_range: "ConvertRange"
    readonly property string cookies: "Cookies"
    readonly property string copy: "Copy"
    readonly property string copy_add: "CopyAdd"
    readonly property string copy_arrow_right: "CopyArrowRight"
    readonly property string copy_select: "CopySelect"
    readonly property string couch: "Couch"
    readonly property string counter: "Counter"
    readonly property string credit_card_clock: "CreditCardClock"
    readonly property string credit_card_person: "CreditCardPerson"
    readonly property string credit_card_toolbox: "CreditCardToolbox"
    readonly property string crop: "Crop"
    readonly property string crop_arrow_rotate: "CropArrowRotate"
    readonly property string crop_interim: "CropInterim"
    readonly property string crop_interim_off: "CropInterimOff"
    readonly property string crop_sparkle: "CropSparkle"
    readonly property string crown: "Crown"
    readonly property string crown_subtract: "CrownSubtract"
    readonly property string cube: "Cube"
    readonly property string cube_add: "CubeAdd"
    readonly property string cube_arrow_curve_down: "CubeArrowCurveDown"
    readonly property string cube_checkmark: "CubeCheckmark"
    readonly property string cube_link: "CubeLink"
    readonly property string cube_multiple: "CubeMultiple"
    readonly property string cube_quick: "CubeQuick"
    readonly property string cube_rotate: "CubeRotate"
    readonly property string cube_sync: "CubeSync"
    readonly property string cube_tree: "CubeTree"
    readonly property string currency_dollar_euro: "CurrencyDollarEuro"
    readonly property string currency_dollar_rupee: "CurrencyDollarRupee"
    readonly property string cursor: "Cursor"
    readonly property string cursor_click: "CursorClick"
    readonly property string cursor_hover: "CursorHover"
    readonly property string cursor_hover_off: "CursorHoverOff"
    readonly property string cursor_prohibited: "CursorProhibited"
    readonly property string cut: "Cut"
    readonly property string dark_theme: "DarkTheme"
    readonly property string data_area: "DataArea"
    readonly property string data_bar_horizontal: "DataBarHorizontal"
    readonly property string data_bar_horizontal_descending: "DataBarHorizontalDescending"
    readonly property string data_bar_vertical: "DataBarVertical"
    readonly property string data_bar_vertical_add: "DataBarVerticalAdd"
    readonly property string data_bar_vertical_arrow_down: "DataBarVerticalArrowDown"
    readonly property string data_bar_vertical_ascending: "DataBarVerticalAscending"
    readonly property string data_bar_vertical_edit: "DataBarVerticalEdit"
    readonly property string data_bar_vertical_star: "DataBarVerticalStar"
    readonly property string database: "Database"
    readonly property string database_arrow_down: "DatabaseArrowDown"
    readonly property string database_arrow_right: "DatabaseArrowRight"
    readonly property string database_arrow_up: "DatabaseArrowUp"
    readonly property string database_checkmark: "DatabaseCheckmark"
    readonly property string database_lightning: "DatabaseLightning"
    readonly property string database_link: "DatabaseLink"
    readonly property string database_multiple: "DatabaseMultiple"
    readonly property string database_person: "DatabasePerson"
    readonly property string database_plug_connected: "DatabasePlugConnected"
    readonly property string database_search: "DatabaseSearch"
    readonly property string database_stack: "DatabaseStack"
    readonly property string database_switch: "DatabaseSwitch"
    readonly property string database_warning: "DatabaseWarning"
    readonly property string database_window: "DatabaseWindow"
    readonly property string data_funnel: "DataFunnel"
    readonly property string data_histogram: "DataHistogram"
    readonly property string data_line: "DataLine"
    readonly property string data_pie: "DataPie"
    readonly property string data_scatter: "DataScatter"
    readonly property string data_sunburst: "DataSunburst"
    readonly property string data_treemap: "DataTreemap"
    readonly property string data_trending: "DataTrending"
    readonly property string data_usage: "DataUsage"
    readonly property string data_usage_checkmark: "DataUsageCheckmark"
    readonly property string data_usage_edit: "DataUsageEdit"
    readonly property string data_usage_settings: "DataUsageSettings"
    readonly property string data_usage_sparkle: "DataUsageSparkle"
    readonly property string data_usage_toolbox: "DataUsageToolbox"
    readonly property string data_waterfall: "DataWaterfall"
    readonly property string data_whisker: "DataWhisker"
    readonly property string decimal_arrow_left: "DecimalArrowLeft"
    readonly property string decimal_arrow_right: "DecimalArrowRight"
    readonly property string icon_delete: "Delete"
    readonly property string delete_arrow_back: "DeleteArrowBack"
    readonly property string delete_dismiss: "DeleteDismiss"
    readonly property string delete_lines: "DeleteLines"
    readonly property string delete_off: "DeleteOff"
    readonly property string dentist: "Dentist"
    readonly property string design_ideas: "DesignIdeas"
    readonly property string desk: "Desk"
    readonly property string desk_multiple: "DeskMultiple"
    readonly property string desk_sparkle: "DeskSparkle"
    readonly property string desktop: "Desktop"
    readonly property string desktop_arrow_down: "DesktopArrowDown"
    readonly property string desktop_arrow_down_off: "DesktopArrowDownOff"
    readonly property string desktop_arrow_right: "DesktopArrowRight"
    readonly property string desktop_checkmark: "DesktopCheckmark"
    readonly property string desktop_cursor: "DesktopCursor"
    readonly property string desktop_edit: "DesktopEdit"
    readonly property string desktop_flow: "DesktopFlow"
    readonly property string desktop_keyboard: "DesktopKeyboard"
    readonly property string desktop_mac: "DesktopMac"
    readonly property string desktop_off: "DesktopOff"
    readonly property string desktop_pulse: "DesktopPulse"
    readonly property string desktop_signal: "DesktopSignal"
    readonly property string desktop_speaker: "DesktopSpeaker"
    readonly property string desktop_speaker_off: "DesktopSpeakerOff"
    readonly property string desktop_sync: "DesktopSync"
    readonly property string desktop_toolbox: "DesktopToolbox"
    readonly property string desktop_tower: "DesktopTower"
    readonly property string developer_board: "DeveloperBoard"
    readonly property string developer_board_lightning: "DeveloperBoardLightning"
    readonly property string developer_board_lightning_toolbox: "DeveloperBoardLightningToolbox"
    readonly property string developer_board_search: "DeveloperBoardSearch"
    readonly property string device_e_q: "DeviceEQ"
    readonly property string device_meeting_room: "DeviceMeetingRoom"
    readonly property string device_meeting_room_all_in_one: "DeviceMeetingRoomAllInOne"
    readonly property string device_meeting_room_bar: "DeviceMeetingRoomBar"
    readonly property string device_meeting_room_remote: "DeviceMeetingRoomRemote"
    readonly property string diagram: "Diagram"
    readonly property string dialpad: "Dialpad"
    readonly property string dialpad_off: "DialpadOff"
    readonly property string dialpad_question_mark: "DialpadQuestionMark"
    readonly property string diamond: "Diamond"
    readonly property string diamond_dismiss: "DiamondDismiss"
    readonly property string diamond_link: "DiamondLink"
    readonly property string directions: "Directions"
    readonly property string dishwasher: "Dishwasher"
    readonly property string dismiss: "Dismiss"
    readonly property string dismiss_circle: "DismissCircle"
    readonly property string dismiss_square: "DismissSquare"
    readonly property string dismiss_square_multiple: "DismissSquareMultiple"
    readonly property string diversity: "Diversity"
    readonly property string divider_short: "DividerShort"
    readonly property string divider_tall: "DividerTall"
    readonly property string dock: "Dock"
    readonly property string dock_row: "DockRow"
    readonly property string doctor: "Doctor"
    readonly property string document: "Document"
    readonly property string document100: "Document100"
    readonly property string document_add: "DocumentAdd"
    readonly property string document_arrow_down: "DocumentArrowDown"
    readonly property string document_arrow_left: "DocumentArrowLeft"
    readonly property string document_arrow_right: "DocumentArrowRight"
    readonly property string document_arrow_up: "DocumentArrowUp"
    readonly property string document_border_print: "DocumentBorderPrint"
    readonly property string document_briefcase: "DocumentBriefcase"
    readonly property string document_bullet_list: "DocumentBulletList"
    readonly property string document_bullet_list_arrow_left: "DocumentBulletListArrowLeft"
    readonly property string document_bullet_list_clock: "DocumentBulletListClock"
    readonly property string document_bullet_list_cube: "DocumentBulletListCube"
    readonly property string document_bullet_list_multiple: "DocumentBulletListMultiple"
    readonly property string document_bullet_list_off: "DocumentBulletListOff"
    readonly property string document_catch_up: "DocumentCatchUp"
    readonly property string document_checkmark: "DocumentCheckmark"
    readonly property string document_chevron_double: "DocumentChevronDouble"
    readonly property string document_code: "DocumentCode"
    readonly property string document_contract: "DocumentContract"
    readonly property string document_copy: "DocumentCopy"
    readonly property string document_c_s: "DocumentCS"
    readonly property string document_c_s_s: "DocumentCSS"
    readonly property string document_c_s_v: "DocumentCSV"
    readonly property string document_cube: "DocumentCube"
    readonly property string document_data: "DocumentData"
    readonly property string document_database: "DocumentDatabase"
    readonly property string document_data_link: "DocumentDataLink"
    readonly property string document_data_lock: "DocumentDataLock"
    readonly property string document_dismiss: "DocumentDismiss"
    readonly property string document_edit: "DocumentEdit"
    readonly property string document_endnote: "DocumentEndnote"
    readonly property string document_error: "DocumentError"
    readonly property string document_fit: "DocumentFit"
    readonly property string document_flowchart: "DocumentFlowchart"
    readonly property string document_folder: "DocumentFolder"
    readonly property string document_footer: "DocumentFooter"
    readonly property string document_footer_dismiss: "DocumentFooterDismiss"
    readonly property string document_f_s: "DocumentFS"
    readonly property string document_globe: "DocumentGlobe"
    readonly property string document_header: "DocumentHeader"
    readonly property string document_header_arrow_down: "DocumentHeaderArrowDown"
    readonly property string document_header_dismiss: "DocumentHeaderDismiss"
    readonly property string document_header_footer: "DocumentHeaderFooter"
    readonly property string document_heart: "DocumentHeart"
    readonly property string document_heart_pulse: "DocumentHeartPulse"
    readonly property string document_image: "DocumentImage"
    readonly property string document_j_a_v_a: "DocumentJAVA"
    readonly property string document_javascript: "DocumentJavascript"
    readonly property string document_j_s: "DocumentJS"
    readonly property string document_key: "DocumentKey"
    readonly property string document_landscape: "DocumentLandscape"
    readonly property string document_landscape_data: "DocumentLandscapeData"
    readonly property string document_landscape_split: "DocumentLandscapeSplit"
    readonly property string document_landscape_split_hint: "DocumentLandscapeSplitHint"
    readonly property string document_lightning: "DocumentLightning"
    readonly property string document_link: "DocumentLink"
    readonly property string document_lock: "DocumentLock"
    readonly property string document_margins: "DocumentMargins"
    readonly property string document_mention: "DocumentMention"
    readonly property string document_multiple: "DocumentMultiple"
    readonly property string document_multiple_percent: "DocumentMultiplePercent"
    readonly property string document_multiple_prohibited: "DocumentMultipleProhibited"
    readonly property string document_multiple_sync: "DocumentMultipleSync"
    readonly property string document_number1: "DocumentNumber1"
    readonly property string document_one_page: "DocumentOnePage"
    readonly property string document_one_page_add: "DocumentOnePageAdd"
    readonly property string document_one_page_beaker: "DocumentOnePageBeaker"
    readonly property string document_one_page_columns: "DocumentOnePageColumns"
    readonly property string document_one_page_link: "DocumentOnePageLink"
    readonly property string document_one_page_multiple: "DocumentOnePageMultiple"
    readonly property string document_one_page_multiple_sparkle: "DocumentOnePageMultipleSparkle"
    readonly property string document_one_page_sparkle: "DocumentOnePageSparkle"
    readonly property string document_page_bottom_center: "DocumentPageBottomCenter"
    readonly property string document_page_bottom_left: "DocumentPageBottomLeft"
    readonly property string document_page_bottom_right: "DocumentPageBottomRight"
    readonly property string document_page_break: "DocumentPageBreak"
    readonly property string document_page_number: "DocumentPageNumber"
    readonly property string document_page_top_center: "DocumentPageTopCenter"
    readonly property string document_page_top_left: "DocumentPageTopLeft"
    readonly property string document_page_top_right: "DocumentPageTopRight"
    readonly property string document_p_d_f: "DocumentPDF"
    readonly property string document_percent: "DocumentPercent"
    readonly property string document_person: "DocumentPerson"
    readonly property string document_pill: "DocumentPill"
    readonly property string document_print: "DocumentPrint"
    readonly property string document_prohibited: "DocumentProhibited"
    readonly property string document_p_y: "DocumentPY"
    readonly property string document_question_mark: "DocumentQuestionMark"
    readonly property string document_queue: "DocumentQueue"
    readonly property string document_queue_add: "DocumentQueueAdd"
    readonly property string document_queue_multiple: "DocumentQueueMultiple"
    readonly property string document_r_b: "DocumentRB"
    readonly property string document_ribbon: "DocumentRibbon"
    readonly property string document_s_a_s_s: "DocumentSASS"
    readonly property string document_save: "DocumentSave"
    readonly property string document_search: "DocumentSearch"
    readonly property string document_settings: "DocumentSettings"
    readonly property string document_signature: "DocumentSignature"
    readonly property string document_sparkle: "DocumentSparkle"
    readonly property string document_split_hint: "DocumentSplitHint"
    readonly property string document_split_hint_off: "DocumentSplitHintOff"
    readonly property string document_square: "DocumentSquare"
    readonly property string document_sync: "DocumentSync"
    readonly property string document_table: "DocumentTable"
    readonly property string document_table_arrow_right: "DocumentTableArrowRight"
    readonly property string document_table_checkmark: "DocumentTableCheckmark"
    readonly property string document_table_cube: "DocumentTableCube"
    readonly property string document_table_search: "DocumentTableSearch"
    readonly property string document_table_truck: "DocumentTableTruck"
    readonly property string document_target: "DocumentTarget"
    readonly property string document_text: "DocumentText"
    readonly property string document_text_clock: "DocumentTextClock"
    readonly property string document_text_extract: "DocumentTextExtract"
    readonly property string document_text_link: "DocumentTextLink"
    readonly property string document_text_toolbox: "DocumentTextToolbox"
    readonly property string document_toolbox: "DocumentToolbox"
    readonly property string document_t_s: "DocumentTS"
    readonly property string document_v_b: "DocumentVB"
    readonly property string document_width: "DocumentWidth"
    readonly property string document_y_m_l: "DocumentYML"
    readonly property string door: "Door"
    readonly property string door_arrow_left: "DoorArrowLeft"
    readonly property string door_arrow_right: "DoorArrowRight"
    readonly property string door_tag: "DoorTag"
    readonly property string double_swipe_down: "DoubleSwipeDown"
    readonly property string double_swipe_up: "DoubleSwipeUp"
    readonly property string double_tap_swipe_down: "DoubleTapSwipeDown"
    readonly property string double_tap_swipe_up: "DoubleTapSwipeUp"
    readonly property string drafts: "Drafts"
    readonly property string drag: "Drag"
    readonly property string drawer: "Drawer"
    readonly property string drawer_add: "DrawerAdd"
    readonly property string drawer_arrow_download: "DrawerArrowDownload"
    readonly property string drawer_dismiss: "DrawerDismiss"
    readonly property string drawer_play: "DrawerPlay"
    readonly property string drawer_subtract: "DrawerSubtract"
    readonly property string draw_image: "DrawImage"
    readonly property string draw_shape: "DrawShape"
    readonly property string draw_text: "DrawText"
    readonly property string drink_beer: "DrinkBeer"
    readonly property string drink_bottle: "DrinkBottle"
    readonly property string drink_bottle_off: "DrinkBottleOff"
    readonly property string drink_coffee: "DrinkCoffee"
    readonly property string drink_margarita: "DrinkMargarita"
    readonly property string drink_to_go: "DrinkToGo"
    readonly property string drink_wine: "DrinkWine"
    readonly property string drive_train: "DriveTrain"
    readonly property string drop: "Drop"
    readonly property string dual_screen: "DualScreen"
    readonly property string dual_screen_add: "DualScreenAdd"
    readonly property string dual_screen_arrow_right: "DualScreenArrowRight"
    readonly property string dual_screen_arrow_up: "DualScreenArrowUp"
    readonly property string dual_screen_clock: "DualScreenClock"
    readonly property string dual_screen_closed_alert: "DualScreenClosedAlert"
    readonly property string dual_screen_desktop: "DualScreenDesktop"
    readonly property string dual_screen_dismiss: "DualScreenDismiss"
    readonly property string dual_screen_group: "DualScreenGroup"
    readonly property string dual_screen_header: "DualScreenHeader"
    readonly property string dual_screen_lock: "DualScreenLock"
    readonly property string dual_screen_mirror: "DualScreenMirror"
    readonly property string dual_screen_pagination: "DualScreenPagination"
    readonly property string dual_screen_settings: "DualScreenSettings"
    readonly property string dual_screen_span: "DualScreenSpan"
    readonly property string dual_screen_speaker: "DualScreenSpeaker"
    readonly property string dual_screen_status_bar: "DualScreenStatusBar"
    readonly property string dual_screen_tablet: "DualScreenTablet"
    readonly property string dual_screen_update: "DualScreenUpdate"
    readonly property string dual_screen_vertical_scroll: "DualScreenVerticalScroll"
    readonly property string dual_screen_vibrate: "DualScreenVibrate"
    readonly property string dumbbell: "Dumbbell"
    readonly property string dust: "Dust"
    readonly property string earth: "Earth"
    readonly property string earth_leaf: "EarthLeaf"
    readonly property string edit: "Edit"
    readonly property string edit_arrow_back: "EditArrowBack"
    readonly property string edit_line_horizontal3: "EditLineHorizontal3"
    readonly property string edit_lock: "EditLock"
    readonly property string edit_off: "EditOff"
    readonly property string edit_person: "EditPerson"
    readonly property string edit_prohibited: "EditProhibited"
    readonly property string edit_settings: "EditSettings"
    readonly property string elevator: "Elevator"
    readonly property string emoji: "Emoji"
    readonly property string emoji_add: "EmojiAdd"
    readonly property string emoji_angry: "EmojiAngry"
    readonly property string emoji_edit: "EmojiEdit"
    readonly property string emoji_hand: "EmojiHand"
    readonly property string emoji_hint: "EmojiHint"
    readonly property string emoji_laugh: "EmojiLaugh"
    readonly property string emoji_meh: "EmojiMeh"
    readonly property string emoji_meme: "EmojiMeme"
    readonly property string emoji_multiple: "EmojiMultiple"
    readonly property string emoji_sad: "EmojiSad"
    readonly property string emoji_sad_slight: "EmojiSadSlight"
    readonly property string emoji_smile_slight: "EmojiSmileSlight"
    readonly property string emoji_sparkle: "EmojiSparkle"
    readonly property string emoji_surprise: "EmojiSurprise"
    readonly property string engine: "Engine"
    readonly property string equal_circle: "EqualCircle"
    readonly property string equal_off: "EqualOff"
    readonly property string eraser: "Eraser"
    readonly property string eraser_medium: "EraserMedium"
    readonly property string eraser_segment: "EraserSegment"
    readonly property string eraser_small: "EraserSmall"
    readonly property string eraser_tool: "EraserTool"
    readonly property string error_circle: "ErrorCircle"
    readonly property string error_circle_settings: "ErrorCircleSettings"
    readonly property string expand_up_left: "ExpandUpLeft"
    readonly property string expand_up_right: "ExpandUpRight"
    readonly property string extended_dock: "ExtendedDock"
    readonly property string eye: "Eye"
    readonly property string eye_circle: "EyeCircle"
    readonly property string eyedropper: "Eyedropper"
    readonly property string eyedropper_off: "EyedropperOff"
    readonly property string eye_lines: "EyeLines"
    readonly property string eye_off: "EyeOff"
    readonly property string eye_tracking: "EyeTracking"
    readonly property string eye_tracking_off: "EyeTrackingOff"
    readonly property string fast_acceleration: "FastAcceleration"
    readonly property string fast_forward: "FastForward"
    readonly property string fax: "Fax"
    readonly property string feed: "Feed"
    readonly property string filmstrip: "Filmstrip"
    readonly property string filmstrip_image: "FilmstripImage"
    readonly property string filmstrip_play: "FilmstripPlay"
    readonly property string filmstrip_split: "FilmstripSplit"
    readonly property string filter: "Filter"
    readonly property string filter_add: "FilterAdd"
    readonly property string filter_dismiss: "FilterDismiss"
    readonly property string filter_sync: "FilterSync"
    readonly property string fingerprint: "Fingerprint"
    readonly property string fire: "Fire"
    readonly property string fireplace: "Fireplace"
    readonly property string fixed_width: "FixedWidth"
    readonly property string flag: "Flag"
    readonly property string flag_checkered: "FlagCheckered"
    readonly property string flag_clock: "FlagClock"
    readonly property string flag_off: "FlagOff"
    readonly property string flash: "Flash"
    readonly property string flash_add: "FlashAdd"
    readonly property string flash_auto: "FlashAuto"
    readonly property string flash_checkmark: "FlashCheckmark"
    readonly property string flash_flow: "FlashFlow"
    readonly property string flashlight: "Flashlight"
    readonly property string flashlight_off: "FlashlightOff"
    readonly property string flash_off: "FlashOff"
    readonly property string flash_play: "FlashPlay"
    readonly property string flash_settings: "FlashSettings"
    readonly property string flash_sparkle: "FlashSparkle"
    readonly property string flip_horizontal: "FlipHorizontal"
    readonly property string flip_vertical: "FlipVertical"
    readonly property string flow: "Flow"
    readonly property string flowchart: "Flowchart"
    readonly property string flowchart_circle: "FlowchartCircle"
    readonly property string flow_dot: "FlowDot"
    readonly property string flow_sparkle: "FlowSparkle"
    readonly property string fluent: "Fluent"
    readonly property string fluid: "Fluid"
    readonly property string folder: "Folder"
    readonly property string folder_add: "FolderAdd"
    readonly property string folder_arrow_left: "FolderArrowLeft"
    readonly property string folder_arrow_right: "FolderArrowRight"
    readonly property string folder_arrow_up: "FolderArrowUp"
    readonly property string folder_briefcase: "FolderBriefcase"
    readonly property string folder_document: "FolderDocument"
    readonly property string folder_globe: "FolderGlobe"
    readonly property string folder_lightning: "FolderLightning"
    readonly property string folder_link: "FolderLink"
    readonly property string folder_list: "FolderList"
    readonly property string folder_mail: "FolderMail"
    readonly property string folder_multiple: "FolderMultiple"
    readonly property string folder_open: "FolderOpen"
    readonly property string folder_open_down: "FolderOpenDown"
    readonly property string folder_open_vertical: "FolderOpenVertical"
    readonly property string folder_people: "FolderPeople"
    readonly property string folder_person: "FolderPerson"
    readonly property string folder_prohibited: "FolderProhibited"
    readonly property string folder_search: "FolderSearch"
    readonly property string folder_swap: "FolderSwap"
    readonly property string folder_sync: "FolderSync"
    readonly property string folder_zip: "FolderZip"
    readonly property string font_decrease: "FontDecrease"
    readonly property string font_increase: "FontIncrease"
    readonly property string font_space_tracking_in: "FontSpaceTrackingIn"
    readonly property string font_space_tracking_out: "FontSpaceTrackingOut"
    readonly property string food: "Food"
    readonly property string food_apple: "FoodApple"
    readonly property string food_cake: "FoodCake"
    readonly property string food_carrot: "FoodCarrot"
    readonly property string food_chicken_leg: "FoodChickenLeg"
    readonly property string food_egg: "FoodEgg"
    readonly property string food_fish: "FoodFish"
    readonly property string food_grains: "FoodGrains"
    readonly property string food_pizza: "FoodPizza"
    readonly property string food_toast: "FoodToast"
    readonly property string form: "Form"
    readonly property string form_multiple: "FormMultiple"
    readonly property string form_multiple_collection: "FormMultipleCollection"
    readonly property string form_new: "FormNew"
    readonly property string form_sparkle: "FormSparkle"
    readonly property string f_p_s120: "FPS120"
    readonly property string f_p_s240: "FPS240"
    readonly property string f_p_s30: "FPS30"
    readonly property string f_p_s60: "FPS60"
    readonly property string f_p_s960: "FPS960"
    readonly property string frame: "Frame"
    readonly property string f_stop: "FStop"
    readonly property string full_screen_maximize: "FullScreenMaximize"
    readonly property string full_screen_minimize: "FullScreenMinimize"
    readonly property string game_chat: "GameChat"
    readonly property string games: "Games"
    readonly property string gantt_chart: "GanttChart"
    readonly property string gas: "Gas"
    readonly property string gas_propane: "GasPropane"
    readonly property string gas_pump: "GasPump"
    readonly property string gather: "Gather"
    readonly property string gauge: "Gauge"
    readonly property string gauge_add: "GaugeAdd"
    readonly property string gavel: "Gavel"
    readonly property string gavel_prohibited: "GavelProhibited"
    readonly property string gesture: "Gesture"
    readonly property string g_i_f: "GIF"
    readonly property string gift: "Gift"
    readonly property string gift_card: "GiftCard"
    readonly property string gift_card_add: "GiftCardAdd"
    readonly property string gift_card_arrow_right: "GiftCardArrowRight"
    readonly property string gift_card_money: "GiftCardMoney"
    readonly property string gift_card_multiple: "GiftCardMultiple"
    readonly property string gift_open: "GiftOpen"
    readonly property string glance: "Glance"
    readonly property string glance_horizontal: "GlanceHorizontal"
    readonly property string glance_horizontal_sparkles: "GlanceHorizontalSparkles"
    readonly property string glasses: "Glasses"
    readonly property string glasses_off: "GlassesOff"
    readonly property string globe: "Globe"
    readonly property string globe_add: "GlobeAdd"
    readonly property string globe_arrow_forward: "GlobeArrowForward"
    readonly property string globe_arrow_up: "GlobeArrowUp"
    readonly property string globe_clock: "GlobeClock"
    readonly property string globe_desktop: "GlobeDesktop"
    readonly property string globe_error: "GlobeError"
    readonly property string globe_location: "GlobeLocation"
    readonly property string globe_off: "GlobeOff"
    readonly property string globe_person: "GlobePerson"
    readonly property string globe_prohibited: "GlobeProhibited"
    readonly property string globe_search: "GlobeSearch"
    readonly property string globe_shield: "GlobeShield"
    readonly property string globe_star: "GlobeStar"
    readonly property string globe_surface: "GlobeSurface"
    readonly property string globe_sync: "GlobeSync"
    readonly property string globe_video: "GlobeVideo"
    readonly property string globe_warning: "GlobeWarning"
    readonly property string grid: "Grid"
    readonly property string grid_circles: "GridCircles"
    readonly property string grid_dots: "GridDots"
    readonly property string grid_kanban: "GridKanban"
    readonly property string group: "Group"
    readonly property string group_dismiss: "GroupDismiss"
    readonly property string group_list: "GroupList"
    readonly property string group_return: "GroupReturn"
    readonly property string guardian: "Guardian"
    readonly property string guest: "Guest"
    readonly property string guest_add: "GuestAdd"
    readonly property string guitar: "Guitar"
    readonly property string hand_draw: "HandDraw"
    readonly property string hand_left: "HandLeft"
    readonly property string hand_left_chat: "HandLeftChat"
    readonly property string hand_multiple: "HandMultiple"
    readonly property string hand_open_heart: "HandOpenHeart"
    readonly property string hand_point: "HandPoint"
    readonly property string hand_right: "HandRight"
    readonly property string hand_right_off: "HandRightOff"
    readonly property string handshake: "Handshake"
    readonly property string hand_wave: "HandWave"
    readonly property string haptic_strong: "HapticStrong"
    readonly property string haptic_weak: "HapticWeak"
    readonly property string hard_drive: "HardDrive"
    readonly property string hard_drive_call: "HardDriveCall"
    readonly property string hat_graduation: "HatGraduation"
    readonly property string hat_graduation_add: "HatGraduationAdd"
    readonly property string hat_graduation_sparkle: "HatGraduationSparkle"
    readonly property string h_d: "HD"
    readonly property string h_d_off: "HDOff"
    readonly property string h_d_r: "HDR"
    readonly property string h_d_r_off: "HDROff"
    readonly property string headphones: "Headphones"
    readonly property string headphones_sound_wave: "HeadphonesSoundWave"
    readonly property string headset: "Headset"
    readonly property string headset_add: "HeadsetAdd"
    readonly property string headset_v_r: "HeadsetVR"
    readonly property string heart: "Heart"
    readonly property string heart_broken: "HeartBroken"
    readonly property string heart_circle: "HeartCircle"
    readonly property string heart_circle_hint: "HeartCircleHint"
    readonly property string heart_off: "HeartOff"
    readonly property string heart_pulse: "HeartPulse"
    readonly property string heart_pulse_checkmark: "HeartPulseCheckmark"
    readonly property string heart_pulse_error: "HeartPulseError"
    readonly property string heart_pulse_warning: "HeartPulseWarning"
    readonly property string hexagon: "Hexagon"
    readonly property string hexagon_sparkle: "HexagonSparkle"
    readonly property string hexagon_three: "HexagonThree"
    readonly property string highlight: "Highlight"
    readonly property string highlight_link: "HighlightLink"
    readonly property string highway: "Highway"
    readonly property string history: "History"
    readonly property string history_dismiss: "HistoryDismiss"
    readonly property string home: "Home"
    readonly property string home_add: "HomeAdd"
    readonly property string home_checkmark: "HomeCheckmark"
    readonly property string home_database: "HomeDatabase"
    readonly property string home_empty: "HomeEmpty"
    readonly property string home_garage: "HomeGarage"
    readonly property string home_heart: "HomeHeart"
    readonly property string home_more: "HomeMore"
    readonly property string home_person: "HomePerson"
    readonly property string home_split: "HomeSplit"
    readonly property string hourglass: "Hourglass"
    readonly property string hourglass_half: "HourglassHalf"
    readonly property string hourglass_one_quarter: "HourglassOneQuarter"
    readonly property string hourglass_three_quarter: "HourglassThreeQuarter"
    readonly property string icons: "Icons"
    readonly property string image: "Image"
    readonly property string image_add: "ImageAdd"
    readonly property string image_alt_text: "ImageAltText"
    readonly property string image_arrow_back: "ImageArrowBack"
    readonly property string image_arrow_counterclockwise: "ImageArrowCounterclockwise"
    readonly property string image_arrow_forward: "ImageArrowForward"
    readonly property string image_border: "ImageBorder"
    readonly property string image_circle: "ImageCircle"
    readonly property string image_copy: "ImageCopy"
    readonly property string image_edit: "ImageEdit"
    readonly property string image_globe: "ImageGlobe"
    readonly property string image_multiple: "ImageMultiple"
    readonly property string image_multiple_off: "ImageMultipleOff"
    readonly property string image_off: "ImageOff"
    readonly property string image_prohibited: "ImageProhibited"
    readonly property string image_reflection: "ImageReflection"
    readonly property string image_search: "ImageSearch"
    readonly property string image_shadow: "ImageShadow"
    readonly property string image_sparkle: "ImageSparkle"
    readonly property string image_split: "ImageSplit"
    readonly property string image_stack: "ImageStack"
    readonly property string image_table: "ImageTable"
    readonly property string immersive_reader: "ImmersiveReader"
    readonly property string important: "Important"
    readonly property string incognito: "Incognito"
    readonly property string info: "Info"
    readonly property string info_shield: "InfoShield"
    readonly property string info_sparkle: "InfoSparkle"
    readonly property string inking_tool: "InkingTool"
    readonly property string ink_stroke: "InkStroke"
    readonly property string ink_stroke_arrow_down: "InkStrokeArrowDown"
    readonly property string ink_stroke_arrow_up_down: "InkStrokeArrowUpDown"
    readonly property string in_private_account: "InPrivateAccount"
    readonly property string insert: "Insert"
    readonly property string i_o_s_arrow: "iOSArrow"
    readonly property string i_o_s_arrow_l_t_r: "iOSArrowLTR"
    readonly property string i_o_s_arrow_r_t_l: "iOSArrowRTL"
    readonly property string i_o_s_chevron_right: "iOSChevronRight"
    readonly property string io_t: "IoT"
    readonly property string io_t_alert: "IoTAlert"
    readonly property string item_compare: "ItemCompare"
    readonly property string java_script: "JavaScript"
    readonly property string joystick: "Joystick"
    readonly property string key: "Key"
    readonly property string keyboard: "Keyboard"
    readonly property string keyboard123: "Keyboard123"
    readonly property string keyboard_dock: "KeyboardDock"
    readonly property string keyboard_layout_float: "KeyboardLayoutFloat"
    readonly property string keyboard_layout_one_handed_left: "KeyboardLayoutOneHandedLeft"
    readonly property string keyboard_layout_resize: "KeyboardLayoutResize"
    readonly property string keyboard_layout_split: "KeyboardLayoutSplit"
    readonly property string keyboard_mouse: "KeyboardMouse"
    readonly property string keyboard_shift: "KeyboardShift"
    readonly property string keyboard_shift_uppercase: "KeyboardShiftUppercase"
    readonly property string keyboard_tab: "KeyboardTab"
    readonly property string key_command: "KeyCommand"
    readonly property string key_multiple: "KeyMultiple"
    readonly property string key_reset: "KeyReset"
    readonly property string kiosk: "Kiosk"
    readonly property string laptop: "Laptop"
    readonly property string laptop_briefcase: "LaptopBriefcase"
    readonly property string laptop_dismiss: "LaptopDismiss"
    readonly property string laptop_multiple: "LaptopMultiple"
    readonly property string laptop_person: "LaptopPerson"
    readonly property string laptop_settings: "LaptopSettings"
    readonly property string laptop_shield: "LaptopShield"
    readonly property string laser_tool: "LaserTool"
    readonly property string lasso: "Lasso"
    readonly property string launcher_settings: "LauncherSettings"
    readonly property string layer: "Layer"
    readonly property string layer_diagonal: "LayerDiagonal"
    readonly property string layer_diagonal_add: "LayerDiagonalAdd"
    readonly property string layer_diagonal_person: "LayerDiagonalPerson"
    readonly property string layer_diagonal_sparkle: "LayerDiagonalSparkle"
    readonly property string layout_add_above: "LayoutAddAbove"
    readonly property string layout_add_below: "LayoutAddBelow"
    readonly property string layout_cell_four: "LayoutCellFour"
    readonly property string layout_column_four: "LayoutColumnFour"
    readonly property string layout_column_one_third_left: "LayoutColumnOneThirdLeft"
    readonly property string layout_column_one_third_right: "LayoutColumnOneThirdRight"
    readonly property string layout_column_one_third_right_hint: "LayoutColumnOneThirdRightHint"
    readonly property string layout_column_three: "LayoutColumnThree"
    readonly property string layout_column_two: "LayoutColumnTwo"
    readonly property string layout_column_two_edit: "LayoutColumnTwoEdit"
    readonly property string layout_column_two_split_left: "LayoutColumnTwoSplitLeft"
    readonly property string layout_column_two_split_right: "LayoutColumnTwoSplitRight"
    readonly property string layout_dynamic: "LayoutDynamic"
    readonly property string layout_row_four: "LayoutRowFour"
    readonly property string layout_row_three: "LayoutRowThree"
    readonly property string layout_row_two: "LayoutRowTwo"
    readonly property string layout_row_two_settings: "LayoutRowTwoSettings"
    readonly property string layout_row_two_split_bottom: "LayoutRowTwoSplitBottom"
    readonly property string layout_row_two_split_top: "LayoutRowTwoSplitTop"
    readonly property string leaf_one: "LeafOne"
    readonly property string leaf_three: "LeafThree"
    readonly property string leaf_two: "LeafTwo"
    readonly property string learning_app: "LearningApp"
    readonly property string library: "Library"
    readonly property string lightbulb: "Lightbulb"
    readonly property string lightbulb_checkmark: "LightbulbCheckmark"
    readonly property string lightbulb_circle: "LightbulbCircle"
    readonly property string lightbulb_filament: "LightbulbFilament"
    readonly property string lightbulb_person: "LightbulbPerson"
    readonly property string likert: "Likert"
    readonly property string line: "Line"
    readonly property string line_dashes: "LineDashes"
    readonly property string line_flow_diagonal_up_right: "LineFlowDiagonalUpRight"
    readonly property string line_horizontal1: "LineHorizontal1"
    readonly property string line_horizontal1_dash_dot_dash: "LineHorizontal1DashDotDash"
    readonly property string line_horizontal1_dashes: "LineHorizontal1Dashes"
    readonly property string line_horizontal1_dot: "LineHorizontal1Dot"
    readonly property string line_horizontal2_dashes_solid: "LineHorizontal2DashesSolid"
    readonly property string line_horizontal3: "LineHorizontal3"
    readonly property string line_horizontal4: "LineHorizontal4"
    readonly property string line_horizontal4_search: "LineHorizontal4Search"
    readonly property string line_horizontal5: "LineHorizontal5"
    readonly property string line_horizontal5_error: "LineHorizontal5Error"
    readonly property string line_style: "LineStyle"
    readonly property string line_style_sketch: "LineStyleSketch"
    readonly property string line_thickness: "LineThickness"
    readonly property string link: "Link"
    readonly property string link_add: "LinkAdd"
    readonly property string link_dismiss: "LinkDismiss"
    readonly property string link_edit: "LinkEdit"
    readonly property string link_multiple: "LinkMultiple"
    readonly property string link_person: "LinkPerson"
    readonly property string link_settings: "LinkSettings"
    readonly property string link_square: "LinkSquare"
    readonly property string link_toolbox: "LinkToolbox"
    readonly property string list: "List"
    readonly property string list_bar: "ListBar"
    readonly property string list_bar_tree: "ListBarTree"
    readonly property string list_bar_tree_offset: "ListBarTreeOffset"
    readonly property string list_r_t_l: "ListRTL"
    readonly property string live: "Live"
    readonly property string live_off: "LiveOff"
    readonly property string local_language: "LocalLanguage"
    readonly property string location: "Location"
    readonly property string location_add: "LocationAdd"
    readonly property string location_add_left: "LocationAddLeft"
    readonly property string location_add_right: "LocationAddRight"
    readonly property string location_add_up: "LocationAddUp"
    readonly property string location_arrow: "LocationArrow"
    readonly property string location_arrow_left: "LocationArrowLeft"
    readonly property string location_arrow_right: "LocationArrowRight"
    readonly property string location_arrow_up: "LocationArrowUp"
    readonly property string location_checkmark: "LocationCheckmark"
    readonly property string location_dismiss: "LocationDismiss"
    readonly property string location_live: "LocationLive"
    readonly property string location_off: "LocationOff"
    readonly property string location_ripple: "LocationRipple"
    readonly property string location_settings: "LocationSettings"
    readonly property string location_target_square: "LocationTargetSquare"
    readonly property string lock_closed: "LockClosed"
    readonly property string lock_closed_key: "LockClosedKey"
    readonly property string lock_closed_ribbon: "LockClosedRibbon"
    readonly property string lock_multiple: "LockMultiple"
    readonly property string lock_open: "LockOpen"
    readonly property string lock_shield: "LockShield"
    readonly property string lottery: "Lottery"
    readonly property string luggage: "Luggage"
    readonly property string mail: "Mail"
    readonly property string mail_add: "MailAdd"
    readonly property string mail_alert: "MailAlert"
    readonly property string mail_all_read: "MailAllRead"
    readonly property string mail_all_unread: "MailAllUnread"
    readonly property string mail_arrow_clockwise: "MailArrowClockwise"
    readonly property string mail_arrow_double_back: "MailArrowDoubleBack"
    readonly property string mail_arrow_down: "MailArrowDown"
    readonly property string mail_arrow_forward: "MailArrowForward"
    readonly property string mail_arrow_up: "MailArrowUp"
    readonly property string mail_attach: "MailAttach"
    readonly property string mailbox: "Mailbox"
    readonly property string mail_checkmark: "MailCheckmark"
    readonly property string mail_clock: "MailClock"
    readonly property string mail_copy: "MailCopy"
    readonly property string mail_data_bar: "MailDataBar"
    readonly property string mail_dismiss: "MailDismiss"
    readonly property string mail_edit: "MailEdit"
    readonly property string mail_error: "MailError"
    readonly property string mail_fish_hook: "MailFishHook"
    readonly property string mail_inbox: "MailInbox"
    readonly property string mail_inbox_add: "MailInboxAdd"
    readonly property string mail_inbox_all: "MailInboxAll"
    readonly property string mail_inbox_arrow_down: "MailInboxArrowDown"
    readonly property string mail_inbox_arrow_right: "MailInboxArrowRight"
    readonly property string mail_inbox_arrow_up: "MailInboxArrowUp"
    readonly property string mail_inbox_checkmark: "MailInboxCheckmark"
    readonly property string mail_inbox_dismiss: "MailInboxDismiss"
    readonly property string mail_inbox_person: "MailInboxPerson"
    readonly property string mail_link: "MailLink"
    readonly property string mail_list: "MailList"
    readonly property string mail_multiple: "MailMultiple"
    readonly property string mail_off: "MailOff"
    readonly property string mail_open_person: "MailOpenPerson"
    readonly property string mail_pause: "MailPause"
    readonly property string mail_prohibited: "MailProhibited"
    readonly property string mail_read: "MailRead"
    readonly property string mail_read_briefcase: "MailReadBriefcase"
    readonly property string mail_read_multiple: "MailReadMultiple"
    readonly property string mail_rewind: "MailRewind"
    readonly property string mail_settings: "MailSettings"
    readonly property string mail_shield: "MailShield"
    readonly property string mail_template: "MailTemplate"
    readonly property string mail_unread: "MailUnread"
    readonly property string mail_warning: "MailWarning"
    readonly property string map: "Map"
    readonly property string map_drive: "MapDrive"
    readonly property string markdown: "Markdown"
    readonly property string match_app_layout: "MatchAppLayout"
    readonly property string math_format_linear: "MathFormatLinear"
    readonly property string math_format_professional: "MathFormatProfessional"
    readonly property string math_formula: "MathFormula"
    readonly property string math_formula_sparkle: "MathFormulaSparkle"
    readonly property string math_symbols: "MathSymbols"
    readonly property string maximize: "Maximize"
    readonly property string meet_now: "MeetNow"
    readonly property string megaphone: "Megaphone"
    readonly property string megaphone_circle: "MegaphoneCircle"
    readonly property string megaphone_loud: "MegaphoneLoud"
    readonly property string megaphone_off: "MegaphoneOff"
    readonly property string memory: "Memory"
    readonly property string mention: "Mention"
    readonly property string mention_arrow_down: "MentionArrowDown"
    readonly property string mention_brackets: "MentionBrackets"
    readonly property string merge: "Merge"
    readonly property string mic: "Mic"
    readonly property string mic_link: "MicLink"
    readonly property string mic_off: "MicOff"
    readonly property string mic_prohibited: "MicProhibited"
    readonly property string mic_pulse: "MicPulse"
    readonly property string mic_pulse_off: "MicPulseOff"
    readonly property string mic_record: "MicRecord"
    readonly property string microscope: "Microscope"
    readonly property string microwave: "Microwave"
    readonly property string mic_settings: "MicSettings"
    readonly property string mic_sparkle: "MicSparkle"
    readonly property string mic_sync: "MicSync"
    readonly property string midi: "Midi"
    readonly property string mobile_optimized: "MobileOptimized"
    readonly property string mold: "Mold"
    readonly property string molecule: "Molecule"
    readonly property string money: "Money"
    readonly property string money_calculator: "MoneyCalculator"
    readonly property string money_dismiss: "MoneyDismiss"
    readonly property string money_hand: "MoneyHand"
    readonly property string money_off: "MoneyOff"
    readonly property string money_settings: "MoneySettings"
    readonly property string more_circle: "MoreCircle"
    readonly property string more_horizontal: "MoreHorizontal"
    readonly property string more_vertical: "MoreVertical"
    readonly property string mountain_location_bottom: "MountainLocationBottom"
    readonly property string mountain_location_top: "MountainLocationTop"
    readonly property string mountain_trail: "MountainTrail"
    readonly property string moviesand_t_v: "MoviesandTV"
    readonly property string multiplier1_2x: "Multiplier1_2x"
    readonly property string multiplier1_5x: "Multiplier1_5x"
    readonly property string multiplier1_8x: "Multiplier1_8x"
    readonly property string multiplier1x: "Multiplier1x"
    readonly property string multiplier2x: "Multiplier2x"
    readonly property string multiplier_5x: "Multiplier_5x"
    readonly property string multiselect_l_t_r: "MultiselectLTR"
    readonly property string multiselect_r_t_l: "MultiselectRTL"
    readonly property string music_note1: "MusicNote1"
    readonly property string music_note2: "MusicNote2"
    readonly property string music_note2_play: "MusicNote2Play"
    readonly property string music_note_off1: "MusicNoteOff1"
    readonly property string music_note_off2: "MusicNoteOff2"
    readonly property string my_location: "MyLocation"
    readonly property string navigation: "Navigation"
    readonly property string navigation_briefcase: "NavigationBriefcase"
    readonly property string navigation_location_target: "NavigationLocationTarget"
    readonly property string navigation_person: "NavigationPerson"
    readonly property string navigation_play: "NavigationPlay"
    readonly property string navigation_unread: "NavigationUnread"
    readonly property string network_adapter: "NetworkAdapter"
    readonly property string network_check: "NetworkCheck"
    readonly property string icon_new: "New"
    readonly property string news: "News"
    readonly property string next: "Next"
    readonly property string next_frame: "NextFrame"
    readonly property string note: "Note"
    readonly property string note_add: "NoteAdd"
    readonly property string notebook: "Notebook"
    readonly property string notebook_add: "NotebookAdd"
    readonly property string notebook_arrow_curve_down: "NotebookArrowCurveDown"
    readonly property string notebook_error: "NotebookError"
    readonly property string notebook_eye: "NotebookEye"
    readonly property string notebook_lightning: "NotebookLightning"
    readonly property string notebook_question_mark: "NotebookQuestionMark"
    readonly property string notebook_section: "NotebookSection"
    readonly property string notebook_section_arrow_right: "NotebookSectionArrowRight"
    readonly property string notebook_subsection: "NotebookSubsection"
    readonly property string notebook_sync: "NotebookSync"
    readonly property string note_edit: "NoteEdit"
    readonly property string notepad: "Notepad"
    readonly property string notepad_edit: "NotepadEdit"
    readonly property string notepad_person: "NotepadPerson"
    readonly property string notepad_person_off: "NotepadPersonOff"
    readonly property string notepad_sparkle: "NotepadSparkle"
    readonly property string note_pin: "NotePin"
    readonly property string number_circle0: "NumberCircle0"
    readonly property string number_circle1: "NumberCircle1"
    readonly property string number_circle2: "NumberCircle2"
    readonly property string number_circle3: "NumberCircle3"
    readonly property string number_circle4: "NumberCircle4"
    readonly property string number_circle5: "NumberCircle5"
    readonly property string number_circle6: "NumberCircle6"
    readonly property string number_circle7: "NumberCircle7"
    readonly property string number_circle8: "NumberCircle8"
    readonly property string number_circle9: "NumberCircle9"
    readonly property string number_row: "NumberRow"
    readonly property string number_symbol: "NumberSymbol"
    readonly property string number_symbol_dismiss: "NumberSymbolDismiss"
    readonly property string number_symbol_square: "NumberSymbolSquare"
    readonly property string open: "Open"
    readonly property string open_folder: "OpenFolder"
    readonly property string open_off: "OpenOff"
    readonly property string options: "Options"
    readonly property string organization: "Organization"
    readonly property string organization_horizontal: "OrganizationHorizontal"
    readonly property string orientation: "Orientation"
    readonly property string oval: "Oval"
    readonly property string oven: "Oven"
    readonly property string padding_down: "PaddingDown"
    readonly property string padding_left: "PaddingLeft"
    readonly property string padding_right: "PaddingRight"
    readonly property string padding_top: "PaddingTop"
    readonly property string page_fit: "PageFit"
    readonly property string paint_brush: "PaintBrush"
    readonly property string paint_brush_arrow_down: "PaintBrushArrowDown"
    readonly property string paint_brush_arrow_up: "PaintBrushArrowUp"
    readonly property string paint_brush_sparkle: "PaintBrushSparkle"
    readonly property string paint_brush_subtract: "PaintBrushSubtract"
    readonly property string paint_bucket: "PaintBucket"
    readonly property string paint_bucket_brush: "PaintBucketBrush"
    readonly property string pair: "Pair"
    readonly property string panel_bottom: "PanelBottom"
    readonly property string panel_bottom_contract: "PanelBottomContract"
    readonly property string panel_bottom_expand: "PanelBottomExpand"
    readonly property string panel_left: "PanelLeft"
    readonly property string panel_left_add: "PanelLeftAdd"
    readonly property string panel_left_contract: "PanelLeftContract"
    readonly property string panel_left_expand: "PanelLeftExpand"
    readonly property string panel_left_header: "PanelLeftHeader"
    readonly property string panel_left_header_add: "PanelLeftHeaderAdd"
    readonly property string panel_left_header_key: "PanelLeftHeaderKey"
    readonly property string panel_left_key: "PanelLeftKey"
    readonly property string panel_left_text: "PanelLeftText"
    readonly property string panel_left_text_add: "PanelLeftTextAdd"
    readonly property string panel_left_text_dismiss: "PanelLeftTextDismiss"
    readonly property string panel_right: "PanelRight"
    readonly property string panel_right_add: "PanelRightAdd"
    readonly property string panel_right_contract: "PanelRightContract"
    readonly property string panel_right_cursor: "PanelRightCursor"
    readonly property string panel_right_expand: "PanelRightExpand"
    readonly property string panel_right_gallery: "PanelRightGallery"
    readonly property string panel_separate_window: "PanelSeparateWindow"
    readonly property string panel_top_contract: "PanelTopContract"
    readonly property string panel_top_expand: "PanelTopExpand"
    readonly property string panel_top_gallery: "PanelTopGallery"
    readonly property string password: "Password"
    readonly property string password_clock: "PasswordClock"
    readonly property string patch: "Patch"
    readonly property string patient: "Patient"
    readonly property string pause: "Pause"
    readonly property string pause_circle: "PauseCircle"
    readonly property string pause_off: "PauseOff"
    readonly property string pause_settings: "PauseSettings"
    readonly property string payment: "Payment"
    readonly property string payment_wireless: "PaymentWireless"
    readonly property string pen: "Pen"
    readonly property string pen_dismiss: "PenDismiss"
    readonly property string pen_off: "PenOff"
    readonly property string pen_prohibited: "PenProhibited"
    readonly property string pen_sparkle: "PenSparkle"
    readonly property string pen_sync: "PenSync"
    readonly property string pentagon: "Pentagon"
    readonly property string people: "People"
    readonly property string people_add: "PeopleAdd"
    readonly property string people_audience: "PeopleAudience"
    readonly property string people_call: "PeopleCall"
    readonly property string people_chat: "PeopleChat"
    readonly property string people_checkmark: "PeopleCheckmark"
    readonly property string people_communication: "PeopleCommunication"
    readonly property string people_community: "PeopleCommunity"
    readonly property string people_community_add: "PeopleCommunityAdd"
    readonly property string people_edit: "PeopleEdit"
    readonly property string people_error: "PeopleError"
    readonly property string people_eye: "PeopleEye"
    readonly property string people_interwoven: "PeopleInterwoven"
    readonly property string people_link: "PeopleLink"
    readonly property string people_list: "PeopleList"
    readonly property string people_lock: "PeopleLock"
    readonly property string people_money: "PeopleMoney"
    readonly property string people_prohibited: "PeopleProhibited"
    readonly property string people_queue: "PeopleQueue"
    readonly property string people_search: "PeopleSearch"
    readonly property string people_settings: "PeopleSettings"
    readonly property string people_star: "PeopleStar"
    readonly property string people_subtract: "PeopleSubtract"
    readonly property string people_swap: "PeopleSwap"
    readonly property string people_sync: "PeopleSync"
    readonly property string people_team: "PeopleTeam"
    readonly property string people_team_add: "PeopleTeamAdd"
    readonly property string people_team_delete: "PeopleTeamDelete"
    readonly property string people_team_toolbox: "PeopleTeamToolbox"
    readonly property string people_toolbox: "PeopleToolbox"
    readonly property string person: "Person"
    readonly property string person5: "Person5"
    readonly property string person6: "Person6"
    readonly property string person_account: "PersonAccount"
    readonly property string person_accounts: "PersonAccounts"
    readonly property string person_add: "PersonAdd"
    readonly property string person_alert: "PersonAlert"
    readonly property string person_alert_off: "PersonAlertOff"
    readonly property string person_arrow_back: "PersonArrowBack"
    readonly property string person_arrow_left: "PersonArrowLeft"
    readonly property string person_arrow_right: "PersonArrowRight"
    readonly property string person_available: "PersonAvailable"
    readonly property string person_board: "PersonBoard"
    readonly property string person_board_add: "PersonBoardAdd"
    readonly property string person_briefcase: "PersonBriefcase"
    readonly property string person_call: "PersonCall"
    readonly property string person_chat: "PersonChat"
    readonly property string person_circle: "PersonCircle"
    readonly property string person_clock: "PersonClock"
    readonly property string person_delete: "PersonDelete"
    readonly property string person_desktop: "PersonDesktop"
    readonly property string person_edit: "PersonEdit"
    readonly property string person_error: "PersonError"
    readonly property string person_feedback: "PersonFeedback"
    readonly property string person_guest: "PersonGuest"
    readonly property string person_head_hint: "PersonHeadHint"
    readonly property string person_heart: "PersonHeart"
    readonly property string person_home: "PersonHome"
    readonly property string person_info: "PersonInfo"
    readonly property string person_key: "PersonKey"
    readonly property string person_lightbulb: "PersonLightbulb"
    readonly property string person_lightning: "PersonLightning"
    readonly property string person_link: "PersonLink"
    readonly property string person_lock: "PersonLock"
    readonly property string person_mail: "PersonMail"
    readonly property string person_money: "PersonMoney"
    readonly property string person_note: "PersonNote"
    readonly property string person_passkey: "PersonPasskey"
    readonly property string person_phone: "PersonPhone"
    readonly property string person_pill: "PersonPill"
    readonly property string person_prohibited: "PersonProhibited"
    readonly property string person_question_mark: "PersonQuestionMark"
    readonly property string person_ribbon: "PersonRibbon"
    readonly property string person_running: "PersonRunning"
    readonly property string person_search: "PersonSearch"
    readonly property string person_settings: "PersonSettings"
    readonly property string person_shield: "PersonShield"
    readonly property string person_sound_spatial: "PersonSoundSpatial"
    readonly property string person_square: "PersonSquare"
    readonly property string person_square_add: "PersonSquareAdd"
    readonly property string person_square_checkmark: "PersonSquareCheckmark"
    readonly property string person_standing: "PersonStanding"
    readonly property string person_star: "PersonStar"
    readonly property string person_starburst: "PersonStarburst"
    readonly property string person_subtract: "PersonSubtract"
    readonly property string person_support: "PersonSupport"
    readonly property string person_swap: "PersonSwap"
    readonly property string person_sync: "PersonSync"
    readonly property string person_tag: "PersonTag"
    readonly property string person_tentative: "PersonTentative"
    readonly property string person_voice: "PersonVoice"
    readonly property string person_walking: "PersonWalking"
    readonly property string person_warning: "PersonWarning"
    readonly property string person_wrench: "PersonWrench"
    readonly property string phone: "Phone"
    readonly property string phone_add: "PhoneAdd"
    readonly property string phone_arrow_right: "PhoneArrowRight"
    readonly property string phone_briefcase: "PhoneBriefcase"
    readonly property string phone_chat: "PhoneChat"
    readonly property string phone_checkmark: "PhoneCheckmark"
    readonly property string phone_desktop: "PhoneDesktop"
    readonly property string phone_desktop_add: "PhoneDesktopAdd"
    readonly property string phone_dismiss: "PhoneDismiss"
    readonly property string phone_edit: "PhoneEdit"
    readonly property string phone_eraser: "PhoneEraser"
    readonly property string phone_footer_arrow_down: "PhoneFooterArrowDown"
    readonly property string phone_header_arrow_up: "PhoneHeaderArrowUp"
    readonly property string phone_key: "PhoneKey"
    readonly property string phone_laptop: "PhoneLaptop"
    readonly property string phone_link_setup: "PhoneLinkSetup"
    readonly property string phone_lock: "PhoneLock"
    readonly property string phone_multiple: "PhoneMultiple"
    readonly property string phone_multiple_settings: "PhoneMultipleSettings"
    readonly property string phone_page_header: "PhonePageHeader"
    readonly property string phone_pagination: "PhonePagination"
    readonly property string phone_person: "PhonePerson"
    readonly property string phone_screen_time: "PhoneScreenTime"
    readonly property string phone_shake: "PhoneShake"
    readonly property string phone_span_in: "PhoneSpanIn"
    readonly property string phone_span_out: "PhoneSpanOut"
    readonly property string phone_speaker: "PhoneSpeaker"
    readonly property string phone_status_bar: "PhoneStatusBar"
    readonly property string phone_subtract: "PhoneSubtract"
    readonly property string phone_tablet: "PhoneTablet"
    readonly property string phone_update: "PhoneUpdate"
    readonly property string phone_update_checkmark: "PhoneUpdateCheckmark"
    readonly property string phone_vertical_scroll: "PhoneVerticalScroll"
    readonly property string phone_vibrate: "PhoneVibrate"
    readonly property string photo_filter: "PhotoFilter"
    readonly property string pi: "Pi"
    readonly property string picture_in_picture: "PictureInPicture"
    readonly property string picture_in_picture_enter: "PictureInPictureEnter"
    readonly property string picture_in_picture_exit: "PictureInPictureExit"
    readonly property string pill: "Pill"
    readonly property string pin: "Pin"
    readonly property string pin_globe: "PinGlobe"
    readonly property string pin_off: "PinOff"
    readonly property string pipeline: "Pipeline"
    readonly property string pipeline_add: "PipelineAdd"
    readonly property string pipeline_arrow_curve_down: "PipelineArrowCurveDown"
    readonly property string pipeline_play: "PipelinePlay"
    readonly property string pivot: "Pivot"
    readonly property string planet: "Planet"
    readonly property string plant_cattail: "PlantCattail"
    readonly property string plant_grass: "PlantGrass"
    readonly property string plant_ragweed: "PlantRagweed"
    readonly property string play: "Play"
    readonly property string play_circle: "PlayCircle"
    readonly property string play_circle_hint: "PlayCircleHint"
    readonly property string play_circle_hint_half: "PlayCircleHintHalf"
    readonly property string play_circle_sparkle: "PlayCircleSparkle"
    readonly property string playing_cards: "PlayingCards"
    readonly property string play_multiple: "PlayMultiple"
    readonly property string play_settings: "PlaySettings"
    readonly property string plug_connected: "PlugConnected"
    readonly property string plug_connected_add: "PlugConnectedAdd"
    readonly property string plug_connected_checkmark: "PlugConnectedCheckmark"
    readonly property string plug_connected_settings: "PlugConnectedSettings"
    readonly property string plug_disconnected: "PlugDisconnected"
    readonly property string point_scan: "PointScan"
    readonly property string poll: "Poll"
    readonly property string poll_horizontal: "PollHorizontal"
    readonly property string poll_off: "PollOff"
    readonly property string port_h_d_m_i: "PortHDMI"
    readonly property string port_micro_u_s_b: "PortMicroUSB"
    readonly property string port_u_s_b_a: "PortUSBA"
    readonly property string port_u_s_b_c: "PortUSBC"
    readonly property string position_backward: "PositionBackward"
    readonly property string position_forward: "PositionForward"
    readonly property string position_to_back: "PositionToBack"
    readonly property string position_to_front: "PositionToFront"
    readonly property string power: "Power"
    readonly property string predictions: "Predictions"
    readonly property string premium: "Premium"
    readonly property string premium_person: "PremiumPerson"
    readonly property string presence_available: "PresenceAvailable"
    readonly property string presence_away: "PresenceAway"
    readonly property string presence_blocked: "PresenceBlocked"
    readonly property string presence_d_n_d: "PresenceDND"
    readonly property string presence_offline: "PresenceOffline"
    readonly property string presence_o_o_f: "PresenceOOF"
    readonly property string presence_tentative: "PresenceTentative"
    readonly property string presence_unknown: "PresenceUnknown"
    readonly property string presenter: "Presenter"
    readonly property string presenter_off: "PresenterOff"
    readonly property string preview_link: "PreviewLink"
    readonly property string previous: "Previous"
    readonly property string previous_frame: "PreviousFrame"
    readonly property string icon_print: "Print"
    readonly property string print_add: "PrintAdd"
    readonly property string production: "Production"
    readonly property string production_checkmark: "ProductionCheckmark"
    readonly property string prohibited: "Prohibited"
    readonly property string prohibited_multiple: "ProhibitedMultiple"
    readonly property string prohibited_note: "ProhibitedNote"
    readonly property string prohibited_smoking: "ProhibitedSmoking"
    readonly property string projection_screen: "ProjectionScreen"
    readonly property string projection_screen_dismiss: "ProjectionScreenDismiss"
    readonly property string projection_screen_text: "ProjectionScreenText"
    readonly property string projection_screen_text_sparkle: "ProjectionScreenTextSparkle"
    readonly property string prompt: "Prompt"
    readonly property string protocol_handler: "ProtocolHandler"
    readonly property string pulse: "Pulse"
    readonly property string pulse_square: "PulseSquare"
    readonly property string puzzle_cube: "PuzzleCube"
    readonly property string puzzle_cube_piece: "PuzzleCubePiece"
    readonly property string puzzle_piece: "PuzzlePiece"
    readonly property string puzzle_piece_shield: "PuzzlePieceShield"
    readonly property string q_r_code: "QRCode"
    readonly property string question: "Question"
    readonly property string question_circle: "QuestionCircle"
    readonly property string quiz: "Quiz"
    readonly property string quiz_new: "QuizNew"
    readonly property string radar: "Radar"
    readonly property string radar_checkmark: "RadarCheckmark"
    readonly property string radar_rectangle_multiple: "RadarRectangleMultiple"
    readonly property string radio_button: "RadioButton"
    readonly property string radio_button_off: "RadioButtonOff"
    readonly property string r_a_m: "RAM"
    readonly property string rating_mature: "RatingMature"
    readonly property string ratio_one_to_one: "RatioOneToOne"
    readonly property string read_aloud: "ReadAloud"
    readonly property string reading_list: "ReadingList"
    readonly property string reading_list_add: "ReadingListAdd"
    readonly property string reading_mode_mobile: "ReadingModeMobile"
    readonly property string real_estate: "RealEstate"
    readonly property string receipt: "Receipt"
    readonly property string receipt_add: "ReceiptAdd"
    readonly property string receipt_bag: "ReceiptBag"
    readonly property string receipt_cube: "ReceiptCube"
    readonly property string receipt_money: "ReceiptMoney"
    readonly property string receipt_play: "ReceiptPlay"
    readonly property string receipt_search: "ReceiptSearch"
    readonly property string receipt_sparkles: "ReceiptSparkles"
    readonly property string record: "Record"
    readonly property string record_stop: "RecordStop"
    readonly property string rectangle_landscape: "RectangleLandscape"
    readonly property string rectangle_landscape_hint_copy: "RectangleLandscapeHintCopy"
    readonly property string rectangle_landscape_sparkle: "RectangleLandscapeSparkle"
    readonly property string rectangle_landscape_sync: "RectangleLandscapeSync"
    readonly property string rectangle_landscape_sync_off: "RectangleLandscapeSyncOff"
    readonly property string rectangle_portrait: "RectanglePortrait"
    readonly property string rectangle_portrait_location_target: "RectanglePortraitLocationTarget"
    readonly property string recycle: "Recycle"
    readonly property string refrigerator: "Refrigerator"
    readonly property string remix_add: "RemixAdd"
    readonly property string remote: "Remote"
    readonly property string rename: "Rename"
    readonly property string rename_a: "RenameA"
    readonly property string re_order: "ReOrder"
    readonly property string re_order_dots_horizontal: "ReOrderDotsHorizontal"
    readonly property string re_order_dots_vertical: "ReOrderDotsVertical"
    readonly property string re_order_vertical: "ReOrderVertical"
    readonly property string replay: "Replay"
    readonly property string resize: "Resize"
    readonly property string resize_image: "ResizeImage"
    readonly property string resize_large: "ResizeLarge"
    readonly property string resize_small: "ResizeSmall"
    readonly property string resize_table: "ResizeTable"
    readonly property string resize_video: "ResizeVideo"
    readonly property string reward: "Reward"
    readonly property string rewind: "Rewind"
    readonly property string rhombus: "Rhombus"
    readonly property string ribbon: "Ribbon"
    readonly property string ribbon_add: "RibbonAdd"
    readonly property string ribbon_off: "RibbonOff"
    readonly property string ribbon_star: "RibbonStar"
    readonly property string road: "Road"
    readonly property string road_cone: "RoadCone"
    readonly property string rocket: "Rocket"
    readonly property string rotate_left: "RotateLeft"
    readonly property string rotate_right: "RotateRight"
    readonly property string router: "Router"
    readonly property string row_child: "RowChild"
    readonly property string row_triple: "RowTriple"
    readonly property string r_s_s: "RSS"
    readonly property string ruler: "Ruler"
    readonly property string run: "Run"
    readonly property string sanitize: "Sanitize"
    readonly property string save: "Save"
    readonly property string save_arrow_right: "SaveArrowRight"
    readonly property string save_copy: "SaveCopy"
    readonly property string save_edit: "SaveEdit"
    readonly property string save_image: "SaveImage"
    readonly property string save_multiple: "SaveMultiple"
    readonly property string save_search: "SaveSearch"
    readonly property string save_sync: "SaveSync"
    readonly property string savings: "Savings"
    readonly property string scale_fill: "ScaleFill"
    readonly property string scale_fit: "ScaleFit"
    readonly property string scales: "Scales"
    readonly property string scan: "Scan"
    readonly property string scan_camera: "ScanCamera"
    readonly property string scan_dash: "ScanDash"
    readonly property string scan_object: "ScanObject"
    readonly property string scan_person: "ScanPerson"
    readonly property string scan_q_r_code: "ScanQRCode"
    readonly property string scan_table: "ScanTable"
    readonly property string scan_text: "ScanText"
    readonly property string scan_thumb_up: "ScanThumbUp"
    readonly property string scan_thumb_up_off: "ScanThumbUpOff"
    readonly property string scan_type: "ScanType"
    readonly property string scan_type_checkmark: "ScanTypeCheckmark"
    readonly property string scan_type_off: "ScanTypeOff"
    readonly property string scratchpad: "Scratchpad"
    readonly property string screen_cut: "ScreenCut"
    readonly property string screen_person: "ScreenPerson"
    readonly property string screen_search: "ScreenSearch"
    readonly property string screenshot: "Screenshot"
    readonly property string screenshot_record: "ScreenshotRecord"
    readonly property string script: "Script"
    readonly property string search: "Search"
    readonly property string search_info: "SearchInfo"
    readonly property string search_settings: "SearchSettings"
    readonly property string search_shield: "SearchShield"
    readonly property string search_sparkle: "SearchSparkle"
    readonly property string search_square: "SearchSquare"
    readonly property string search_visual: "SearchVisual"
    readonly property string seat: "Seat"
    readonly property string seat_add: "SeatAdd"
    readonly property string seat_multiple_stadium: "SeatMultipleStadium"
    readonly property string select_all_off: "SelectAllOff"
    readonly property string select_all_on: "SelectAllOn"
    readonly property string select_object: "SelectObject"
    readonly property string select_object_skew: "SelectObjectSkew"
    readonly property string select_object_skew_dismiss: "SelectObjectSkewDismiss"
    readonly property string select_object_skew_edit: "SelectObjectSkewEdit"
    readonly property string send: "Send"
    readonly property string send_beaker: "SendBeaker"
    readonly property string send_clock: "SendClock"
    readonly property string send_copy: "SendCopy"
    readonly property string send_person: "SendPerson"
    readonly property string serial_port: "SerialPort"
    readonly property string server: "Server"
    readonly property string server_link: "ServerLink"
    readonly property string server_multiple: "ServerMultiple"
    readonly property string server_play: "ServerPlay"
    readonly property string server_surface: "ServerSurface"
    readonly property string server_surface_multiple: "ServerSurfaceMultiple"
    readonly property string service_bell: "ServiceBell"
    readonly property string settings: "Settings"
    readonly property string settings_chat: "SettingsChat"
    readonly property string settings_cog_multiple: "SettingsCogMultiple"
    readonly property string shape_exclude: "ShapeExclude"
    readonly property string shape_intersect: "ShapeIntersect"
    readonly property string shape_organic: "ShapeOrganic"
    readonly property string shapes: "Shapes"
    readonly property string shape_subtract: "ShapeSubtract"
    readonly property string shape_union: "ShapeUnion"
    readonly property string share: "Share"
    readonly property string share_android: "ShareAndroid"
    readonly property string share_close_tray: "ShareCloseTray"
    readonly property string sharei_o_s: "ShareiOS"
    readonly property string share_multiple: "ShareMultiple"
    readonly property string share_screen_person: "ShareScreenPerson"
    readonly property string share_screen_person_overlay: "ShareScreenPersonOverlay"
    readonly property string share_screen_person_overlay_inside: "ShareScreenPersonOverlayInside"
    readonly property string share_screen_person_p: "ShareScreenPersonP"
    readonly property string share_screen_start: "ShareScreenStart"
    readonly property string share_screen_stop: "ShareScreenStop"
    readonly property string shield: "Shield"
    readonly property string shield_add: "ShieldAdd"
    readonly property string shield_arrow_right: "ShieldArrowRight"
    readonly property string shield_badge: "ShieldBadge"
    readonly property string shield_checkmark: "ShieldCheckmark"
    readonly property string shield_dismiss: "ShieldDismiss"
    readonly property string shield_dismiss_shield: "ShieldDismissShield"
    readonly property string shield_error: "ShieldError"
    readonly property string shield_globe: "ShieldGlobe"
    readonly property string shield_keyhole: "ShieldKeyhole"
    readonly property string shield_lock: "ShieldLock"
    readonly property string shield_person: "ShieldPerson"
    readonly property string shield_person_add: "ShieldPersonAdd"
    readonly property string shield_prohibited: "ShieldProhibited"
    readonly property string shield_question: "ShieldQuestion"
    readonly property string shield_settings: "ShieldSettings"
    readonly property string shield_task: "ShieldTask"
    readonly property string shifts: "Shifts"
    readonly property string shifts30_minutes: "Shifts30Minutes"
    readonly property string shifts_activity: "ShiftsActivity"
    readonly property string shifts_add: "ShiftsAdd"
    readonly property string shifts_availability: "ShiftsAvailability"
    readonly property string shifts_checkmark: "ShiftsCheckmark"
    readonly property string shifts_day: "ShiftsDay"
    readonly property string shifts_open: "ShiftsOpen"
    readonly property string shifts_prohibited: "ShiftsProhibited"
    readonly property string shifts_question_mark: "ShiftsQuestionMark"
    readonly property string shifts_team: "ShiftsTeam"
    readonly property string shopping_bag: "ShoppingBag"
    readonly property string shopping_bag_add: "ShoppingBagAdd"
    readonly property string shopping_bag_arrow_left: "ShoppingBagArrowLeft"
    readonly property string shopping_bag_checkmark: "ShoppingBagCheckmark"
    readonly property string shopping_bag_dismiss: "ShoppingBagDismiss"
    readonly property string shopping_bag_pause: "ShoppingBagPause"
    readonly property string shopping_bag_percent: "ShoppingBagPercent"
    readonly property string shopping_bag_play: "ShoppingBagPlay"
    readonly property string shopping_bag_tag: "ShoppingBagTag"
    readonly property string shortpick: "Shortpick"
    readonly property string showerhead: "Showerhead"
    readonly property string sidebar_search_l_t_r: "SidebarSearchLTR"
    readonly property string sidebar_search_r_t_l: "SidebarSearchRTL"
    readonly property string signature: "Signature"
    readonly property string sign_out: "SignOut"
    readonly property string s_i_m: "SIM"
    readonly property string sine_wave_dots: "SineWaveDots"
    readonly property string skip_back10: "SkipBack10"
    readonly property string skip_back15: "SkipBack15"
    readonly property string skip_forward10: "SkipForward10"
    readonly property string skip_forward15: "SkipForward15"
    readonly property string skip_forward30: "SkipForward30"
    readonly property string skip_forward_tab: "SkipForwardTab"
    readonly property string slash_forward: "SlashForward"
    readonly property string sleep: "Sleep"
    readonly property string slide_add: "SlideAdd"
    readonly property string slide_arrow_right: "SlideArrowRight"
    readonly property string slide_content: "SlideContent"
    readonly property string slide_eraser: "SlideEraser"
    readonly property string slide_grid: "SlideGrid"
    readonly property string slide_hide: "SlideHide"
    readonly property string slide_layout: "SlideLayout"
    readonly property string slide_link: "SlideLink"
    readonly property string slide_microphone: "SlideMicrophone"
    readonly property string slide_multiple: "SlideMultiple"
    readonly property string slide_multiple_arrow_right: "SlideMultipleArrowRight"
    readonly property string slide_multiple_search: "SlideMultipleSearch"
    readonly property string slide_play: "SlidePlay"
    readonly property string slide_record: "SlideRecord"
    readonly property string slide_search: "SlideSearch"
    readonly property string slide_settings: "SlideSettings"
    readonly property string slide_size: "SlideSize"
    readonly property string slide_text: "SlideText"
    readonly property string slide_text_call: "SlideTextCall"
    readonly property string slide_text_cursor: "SlideTextCursor"
    readonly property string slide_text_edit: "SlideTextEdit"
    readonly property string slide_text_multiple: "SlideTextMultiple"
    readonly property string slide_text_person: "SlideTextPerson"
    readonly property string slide_text_sparkle: "SlideTextSparkle"
    readonly property string slide_text_title: "SlideTextTitle"
    readonly property string slide_text_title_add: "SlideTextTitleAdd"
    readonly property string slide_text_title_checkmark: "SlideTextTitleCheckmark"
    readonly property string slide_text_title_edit: "SlideTextTitleEdit"
    readonly property string slide_topic_add: "SlideTopicAdd"
    readonly property string slide_transition: "SlideTransition"
    readonly property string smartwatch: "Smartwatch"
    readonly property string smartwatch_dot: "SmartwatchDot"
    readonly property string snooze: "Snooze"
    readonly property string sound_source: "SoundSource"
    readonly property string sound_wave_circle: "SoundWaveCircle"
    readonly property string sound_wave_circle_add: "SoundWaveCircleAdd"
    readonly property string sound_wave_circle_sparkle: "SoundWaveCircleSparkle"
    readonly property string sound_wave_circle_subtract: "SoundWaveCircleSubtract"
    readonly property string space3_d: "Space3D"
    readonly property string spacebar: "Spacebar"
    readonly property string sparkle: "Sparkle"
    readonly property string sparkle_action: "SparkleAction"
    readonly property string sparkle_circle: "SparkleCircle"
    readonly property string sparkle_info: "SparkleInfo"
    readonly property string spatula_spoon: "SpatulaSpoon"
    readonly property string speaker0: "Speaker0"
    readonly property string speaker1: "Speaker1"
    readonly property string speaker2: "Speaker2"
    readonly property string speaker_bluetooth: "SpeakerBluetooth"
    readonly property string speaker_box: "SpeakerBox"
    readonly property string speaker_edit: "SpeakerEdit"
    readonly property string speaker_mute: "SpeakerMute"
    readonly property string speaker_off: "SpeakerOff"
    readonly property string speaker_settings: "SpeakerSettings"
    readonly property string speaker_u_s_b: "SpeakerUSB"
    readonly property string spinneri_o_s: "SpinneriOS"
    readonly property string split_hint: "SplitHint"
    readonly property string split_horizontal: "SplitHorizontal"
    readonly property string split_vertical: "SplitVertical"
    readonly property string sport: "Sport"
    readonly property string sport_american_football: "SportAmericanFootball"
    readonly property string sport_baseball: "SportBaseball"
    readonly property string sport_basketball: "SportBasketball"
    readonly property string sport_cricket_ball: "SportCricketBall"
    readonly property string sport_cricket_bat: "SportCricketBat"
    readonly property string sport_hockey: "SportHockey"
    readonly property string sport_soccer: "SportSoccer"
    readonly property string spray_can: "SprayCan"
    readonly property string square: "Square"
    readonly property string square_add: "SquareAdd"
    readonly property string square_arrow_forward: "SquareArrowForward"
    readonly property string square_dismiss: "SquareDismiss"
    readonly property string square_dovetail_joint: "SquareDovetailJoint"
    readonly property string square_eraser: "SquareEraser"
    readonly property string square_hint: "SquareHint"
    readonly property string square_hint_apps: "SquareHintApps"
    readonly property string square_hint_arrow_back: "SquareHintArrowBack"
    readonly property string square_hint_hexagon: "SquareHintHexagon"
    readonly property string square_hint_sparkles: "SquareHintSparkles"
    readonly property string square_multiple: "SquareMultiple"
    readonly property string square_shadow: "SquareShadow"
    readonly property string squares_nested: "SquaresNested"
    readonly property string square_text_arrow_repeat_all: "SquareTextArrowRepeatAll"
    readonly property string stack: "Stack"
    readonly property string stack_add: "StackAdd"
    readonly property string stack_arrow_forward: "StackArrowForward"
    readonly property string stack_off: "StackOff"
    readonly property string stack_star: "StackStar"
    readonly property string stack_vertical: "StackVertical"
    readonly property string star: "Star"
    readonly property string star_add: "StarAdd"
    readonly property string star_arrow_back: "StarArrowBack"
    readonly property string star_arrow_right_end: "StarArrowRightEnd"
    readonly property string star_arrow_right_start: "StarArrowRightStart"
    readonly property string star_checkmark: "StarCheckmark"
    readonly property string star_dismiss: "StarDismiss"
    readonly property string star_edit: "StarEdit"
    readonly property string star_emphasis: "StarEmphasis"
    readonly property string star_filled: "StarFilled"
    readonly property string star_half: "StarHalf"
    readonly property string star_line_horizontal3: "StarLineHorizontal3"
    readonly property string star_off: "StarOff"
    readonly property string star_one_quarter: "StarOneQuarter"
    readonly property string star_outline: "StarOutline"
    readonly property string star_prohibited: "StarProhibited"
    readonly property string star_settings: "StarSettings"
    readonly property string star_three_quarter: "StarThreeQuarter"
    readonly property string status: "Status"
    readonly property string step: "Step"
    readonly property string steps: "Steps"
    readonly property string stethoscope: "Stethoscope"
    readonly property string sticker: "Sticker"
    readonly property string sticker_add: "StickerAdd"
    readonly property string stop: "Stop"
    readonly property string storage: "Storage"
    readonly property string store_microsoft: "StoreMicrosoft"
    readonly property string stove: "Stove"
    readonly property string stream: "Stream"
    readonly property string stream_input: "StreamInput"
    readonly property string stream_input_output: "StreamInputOutput"
    readonly property string stream_output: "StreamOutput"
    readonly property string street_sign: "StreetSign"
    readonly property string style_guide: "StyleGuide"
    readonly property string sub_grid: "SubGrid"
    readonly property string subtitles: "Subtitles"
    readonly property string subtract: "Subtract"
    readonly property string subtract_circle: "SubtractCircle"
    readonly property string subtract_circle_arrow_back: "SubtractCircleArrowBack"
    readonly property string subtract_circle_arrow_forward: "SubtractCircleArrowForward"
    readonly property string subtract_parentheses: "SubtractParentheses"
    readonly property string subtract_square: "SubtractSquare"
    readonly property string subtract_square_multiple: "SubtractSquareMultiple"
    readonly property string surface_earbuds: "SurfaceEarbuds"
    readonly property string surface_hub: "SurfaceHub"
    readonly property string swimming_pool: "SwimmingPool"
    readonly property string swipe_down: "SwipeDown"
    readonly property string swipe_right: "SwipeRight"
    readonly property string swipe_up: "SwipeUp"
    readonly property string symbols: "Symbols"
    readonly property string sync_off: "SyncOff"
    readonly property string syringe: "Syringe"
    readonly property string system: "System"
    readonly property string tab: "Tab"
    readonly property string tab_add: "TabAdd"
    readonly property string tab_arrow_left: "TabArrowLeft"
    readonly property string tab_desktop: "TabDesktop"
    readonly property string tab_desktop_arrow_clockwise: "TabDesktopArrowClockwise"
    readonly property string tab_desktop_arrow_left: "TabDesktopArrowLeft"
    readonly property string tab_desktop_bottom: "TabDesktopBottom"
    readonly property string tab_desktop_clock: "TabDesktopClock"
    readonly property string tab_desktop_copy: "TabDesktopCopy"
    readonly property string tab_desktop_image: "TabDesktopImage"
    readonly property string tab_desktop_link: "TabDesktopLink"
    readonly property string tab_desktop_multiple: "TabDesktopMultiple"
    readonly property string tab_desktop_multiple_add: "TabDesktopMultipleAdd"
    readonly property string tab_desktop_multiple_bottom: "TabDesktopMultipleBottom"
    readonly property string tab_desktop_multiple_sparkle: "TabDesktopMultipleSparkle"
    readonly property string tab_desktop_new_page: "TabDesktopNewPage"
    readonly property string tab_desktop_search: "TabDesktopSearch"
    readonly property string tab_group: "TabGroup"
    readonly property string tab_in_private: "TabInPrivate"
    readonly property string tab_in_private_account: "TabInPrivateAccount"
    readonly property string table: "Table"
    readonly property string table_add: "TableAdd"
    readonly property string table_alt_text: "TableAltText"
    readonly property string table_arrow_repeat_all: "TableArrowRepeatAll"
    readonly property string table_arrow_up: "TableArrowUp"
    readonly property string table_bottom_row: "TableBottomRow"
    readonly property string table_calculator: "TableCalculator"
    readonly property string table_cell_add: "TableCellAdd"
    readonly property string table_cell_center: "TableCellCenter"
    readonly property string table_cell_center_arrow_repeat_all: "TableCellCenterArrowRepeatAll"
    readonly property string table_cell_center_edit: "TableCellCenterEdit"
    readonly property string table_cell_center_link: "TableCellCenterLink"
    readonly property string table_cell_center_search: "TableCellCenterSearch"
    readonly property string table_cell_edit: "TableCellEdit"
    readonly property string table_cells_merge: "TableCellsMerge"
    readonly property string table_cells_split: "TableCellsSplit"
    readonly property string table_checker: "TableChecker"
    readonly property string table_column_top_bottom: "TableColumnTopBottom"
    readonly property string table_column_top_bottom_arrow_repeat_all: "TableColumnTopBottomArrowRepeatAll"
    readonly property string table_column_top_bottom_edit: "TableColumnTopBottomEdit"
    readonly property string table_column_top_bottom_link: "TableColumnTopBottomLink"
    readonly property string table_column_top_bottom_search: "TableColumnTopBottomSearch"
    readonly property string table_copy: "TableCopy"
    readonly property string table_cursor: "TableCursor"
    readonly property string table_delete_column: "TableDeleteColumn"
    readonly property string table_delete_row: "TableDeleteRow"
    readonly property string table_dismiss: "TableDismiss"
    readonly property string table_edit: "TableEdit"
    readonly property string table_freeze_column: "TableFreezeColumn"
    readonly property string table_freeze_column_and_row: "TableFreezeColumnAndRow"
    readonly property string table_freeze_column_and_row_dismiss: "TableFreezeColumnAndRowDismiss"
    readonly property string table_freeze_column_and_row_temp_l_t_r: "TableFreezeColumnAndRowTempLTR"
    readonly property string table_freeze_column_and_row_temp_r_t_l: "TableFreezeColumnAndRowTempRTL"
    readonly property string table_freeze_column_dismiss: "TableFreezeColumnDismiss"
    readonly property string table_freeze_column_temp_l_t_r: "TableFreezeColumnTempLTR"
    readonly property string table_freeze_column_temp_r_t_l: "TableFreezeColumnTempRTL"
    readonly property string table_freeze_row: "TableFreezeRow"
    readonly property string table_freeze_row_dismiss: "TableFreezeRowDismiss"
    readonly property string table_image: "TableImage"
    readonly property string table_insert_column: "TableInsertColumn"
    readonly property string table_insert_row: "TableInsertRow"
    readonly property string table_lightning: "TableLightning"
    readonly property string table_link: "TableLink"
    readonly property string table_lock: "TableLock"
    readonly property string table_move_above: "TableMoveAbove"
    readonly property string table_move_below: "TableMoveBelow"
    readonly property string table_move_left: "TableMoveLeft"
    readonly property string table_move_right: "TableMoveRight"
    readonly property string table_multiple: "TableMultiple"
    readonly property string table_offset: "TableOffset"
    readonly property string table_offset_add: "TableOffsetAdd"
    readonly property string table_offset_less_than_or_equal_to: "TableOffsetLessThanOrEqualTo"
    readonly property string table_offset_settings: "TableOffsetSettings"
    readonly property string table_picnic: "TablePicnic"
    readonly property string table_resize_column: "TableResizeColumn"
    readonly property string table_resize_row: "TableResizeRow"
    readonly property string table_search: "TableSearch"
    readonly property string table_settings: "TableSettings"
    readonly property string table_simple: "TableSimple"
    readonly property string table_simple_checkmark: "TableSimpleCheckmark"
    readonly property string table_simple_exclude: "TableSimpleExclude"
    readonly property string table_simple_include: "TableSimpleInclude"
    readonly property string table_simple_multiple: "TableSimpleMultiple"
    readonly property string table_sparkle: "TableSparkle"
    readonly property string table_split: "TableSplit"
    readonly property string table_stack_above: "TableStackAbove"
    readonly property string table_stack_below: "TableStackBelow"
    readonly property string table_stack_left: "TableStackLeft"
    readonly property string table_stack_right: "TableStackRight"
    readonly property string table_switch: "TableSwitch"
    readonly property string tablet: "Tablet"
    readonly property string tablet_laptop: "TabletLaptop"
    readonly property string tablet_speaker: "TabletSpeaker"
    readonly property string tab_prohibited: "TabProhibited"
    readonly property string tabs: "Tabs"
    readonly property string tab_shield_dismiss: "TabShieldDismiss"
    readonly property string tag: "Tag"
    readonly property string tag_add: "TagAdd"
    readonly property string tag_circle: "TagCircle"
    readonly property string tag_dismiss: "TagDismiss"
    readonly property string tag_edit: "TagEdit"
    readonly property string tag_error: "TagError"
    readonly property string tag_lock: "TagLock"
    readonly property string tag_multiple: "TagMultiple"
    readonly property string tag_off: "TagOff"
    readonly property string tag_percent: "TagPercent"
    readonly property string tag_question_mark: "TagQuestionMark"
    readonly property string tag_reset: "TagReset"
    readonly property string tag_search: "TagSearch"
    readonly property string tap_double: "TapDouble"
    readonly property string tap_single: "TapSingle"
    readonly property string target: "Target"
    readonly property string target_add: "TargetAdd"
    readonly property string target_arrow: "TargetArrow"
    readonly property string target_dismiss: "TargetDismiss"
    readonly property string target_edit: "TargetEdit"
    readonly property string target_sparkle: "TargetSparkle"
    readonly property string task_list_add: "TaskListAdd"
    readonly property string task_list_l_t_r: "TaskListLTR"
    readonly property string task_list_r_t_l: "TaskListRTL"
    readonly property string task_list_square_add: "TaskListSquareAdd"
    readonly property string task_list_square_database: "TaskListSquareDatabase"
    readonly property string task_list_square_l_t_r: "TaskListSquareLTR"
    readonly property string task_list_square_person: "TaskListSquarePerson"
    readonly property string task_list_square_r_t_l: "TaskListSquareRTL"
    readonly property string task_list_square_settings: "TaskListSquareSettings"
    readonly property string task_list_square_sparkle: "TaskListSquareSparkle"
    readonly property string tasks_app: "TasksApp"
    readonly property string teaching: "Teaching"
    readonly property string teardrop_bottom_right: "TeardropBottomRight"
    readonly property string teddy: "Teddy"
    readonly property string temperature: "Temperature"
    readonly property string temperature_degree_celsius: "TemperatureDegreeCelsius"
    readonly property string temperature_degree_fahrenheit: "TemperatureDegreeFahrenheit"
    readonly property string tent: "Tent"
    readonly property string tetris_app: "TetrisApp"
    readonly property string text: "Text"
    readonly property string text_bold: "TextBold"
    readonly property string text_description: "TextDescription"
    readonly property string text_description_l_t_r: "TextDescriptionLTR"
    readonly property string text_description_r_t_l: "TextDescriptionRTL"
    readonly property string text_proofing_tools: "TextProofingTools"
    readonly property string text_proofing_tools_abc: "TextProofingToolsAbc"
    readonly property string text_proofing_tools_ga_na_da: "TextProofingToolsGaNaDa"
    readonly property string text_proofing_tools_zi: "TextProofingToolsZi"
    readonly property string thinking: "Thinking"
    readonly property string thumb_dislike: "ThumbDislike"
    readonly property string thumb_like: "ThumbLike"
    readonly property string thumb_like_dislike: "ThumbLikeDislike"
    readonly property string ticket_diagonal: "TicketDiagonal"
    readonly property string ticket_horizontal: "TicketHorizontal"
    readonly property string time_and_weather: "TimeAndWeather"
    readonly property string timeline: "Timeline"
    readonly property string time_picker: "TimePicker"
    readonly property string timer: "Timer"
    readonly property string timer10: "Timer10"
    readonly property string timer2: "Timer2"
    readonly property string timer3: "Timer3"
    readonly property string timer_off: "TimerOff"
    readonly property string toggle_left: "ToggleLeft"
    readonly property string toggle_multiple: "ToggleMultiple"
    readonly property string toggle_right: "ToggleRight"
    readonly property string toilet: "Toilet"
    readonly property string toolbox: "Toolbox"
    readonly property string tooltip_quote: "TooltipQuote"
    readonly property string tooltip_quote_off: "TooltipQuoteOff"
    readonly property string top_speed: "TopSpeed"
    readonly property string translate: "Translate"
    readonly property string translate_auto: "TranslateAuto"
    readonly property string translate_off: "TranslateOff"
    readonly property string transmission: "Transmission"
    readonly property string transparency_square: "TransparencySquare"
    readonly property string tray_item_add: "TrayItemAdd"
    readonly property string tray_item_remove: "TrayItemRemove"
    readonly property string tree_deciduous: "TreeDeciduous"
    readonly property string tree_evergreen: "TreeEvergreen"
    readonly property string triangle: "Triangle"
    readonly property string triangle_down: "TriangleDown"
    readonly property string triangle_left: "TriangleLeft"
    readonly property string triangle_right: "TriangleRight"
    readonly property string triangle_up: "TriangleUp"
    readonly property string trophy: "Trophy"
    readonly property string trophy_lock: "TrophyLock"
    readonly property string trophy_off: "TrophyOff"
    readonly property string t_v: "TV"
    readonly property string t_v_arrow_right: "TVArrowRight"
    readonly property string t_v_u_s_b: "TVUSB"
    readonly property string umbrella: "Umbrella"
    readonly property string uninstall_app: "UninstallApp"
    readonly property string u_s_b_plug: "USBPlug"
    readonly property string usb_stick: "UsbStick"
    readonly property string vault: "Vault"
    readonly property string vehicle_bicycle: "VehicleBicycle"
    readonly property string vehicle_bus: "VehicleBus"
    readonly property string vehicle_cab: "VehicleCab"
    readonly property string vehicle_cable_car: "VehicleCableCar"
    readonly property string vehicle_car: "VehicleCar"
    readonly property string vehicle_car_collision: "VehicleCarCollision"
    readonly property string vehicle_car_parking: "VehicleCarParking"
    readonly property string vehicle_car_profile: "VehicleCarProfile"
    readonly property string vehicle_car_profile_l_t_r: "VehicleCarProfileLTR"
    readonly property string vehicle_car_profile_l_t_r_clock: "VehicleCarProfileLTRClock"
    readonly property string vehicle_car_profile_r_t_l: "VehicleCarProfileRTL"
    readonly property string vehicle_motorcycle: "VehicleMotorcycle"
    readonly property string vehicle_r_v: "VehicleRV"
    readonly property string vehicle_ship: "VehicleShip"
    readonly property string vehicle_subway: "VehicleSubway"
    readonly property string vehicle_subway_clock: "VehicleSubwayClock"
    readonly property string vehicle_tractor: "VehicleTractor"
    readonly property string vehicle_trailer: "VehicleTrailer"
    readonly property string vehicle_trailer_arrow_down: "VehicleTrailerArrowDown"
    readonly property string vehicle_truck: "VehicleTruck"
    readonly property string vehicle_truck_bag: "VehicleTruckBag"
    readonly property string vehicle_truck_checkmark: "VehicleTruckCheckmark"
    readonly property string vehicle_truck_cube: "VehicleTruckCube"
    readonly property string vehicle_truck_profile: "VehicleTruckProfile"
    readonly property string video: "Video"
    readonly property string video360: "Video360"
    readonly property string video360_off: "Video360Off"
    readonly property string video_add: "VideoAdd"
    readonly property string video_background_effect: "VideoBackgroundEffect"
    readonly property string video_background_effect_horizontal: "VideoBackgroundEffectHorizontal"
    readonly property string video_bluetooth: "VideoBluetooth"
    readonly property string video_chat: "VideoChat"
    readonly property string video_link: "VideoLink"
    readonly property string video_multiple: "VideoMultiple"
    readonly property string video_off: "VideoOff"
    readonly property string video_person: "VideoPerson"
    readonly property string video_person_call: "VideoPersonCall"
    readonly property string video_person_clock: "VideoPersonClock"
    readonly property string video_person_off: "VideoPersonOff"
    readonly property string video_person_pulse: "VideoPersonPulse"
    readonly property string video_person_sparkle: "VideoPersonSparkle"
    readonly property string video_person_sparkle_off: "VideoPersonSparkleOff"
    readonly property string video_person_star: "VideoPersonStar"
    readonly property string video_person_star_off: "VideoPersonStarOff"
    readonly property string video_play_pause: "VideoPlayPause"
    readonly property string video_prohibited: "VideoProhibited"
    readonly property string video_recording: "VideoRecording"
    readonly property string video_security: "VideoSecurity"
    readonly property string video_settings: "VideoSettings"
    readonly property string video_short: "VideoShort"
    readonly property string video_short_multiple: "VideoShortMultiple"
    readonly property string video_switch: "VideoSwitch"
    readonly property string video_sync: "VideoSync"
    readonly property string video_u_s_b: "VideoUSB"
    readonly property string view_desktop: "ViewDesktop"
    readonly property string view_desktop_mobile: "ViewDesktopMobile"
    readonly property string virtual_network: "VirtualNetwork"
    readonly property string virtual_network_toolbox: "VirtualNetworkToolbox"
    readonly property string voicemail: "Voicemail"
    readonly property string voicemail_arrow_back: "VoicemailArrowBack"
    readonly property string voicemail_arrow_forward: "VoicemailArrowForward"
    readonly property string voicemail_arrow_subtract: "VoicemailArrowSubtract"
    readonly property string voicemail_shield: "VoicemailShield"
    readonly property string voicemail_subtract: "VoicemailSubtract"
    readonly property string vote: "Vote"
    readonly property string walkie_talkie: "WalkieTalkie"
    readonly property string wallet: "Wallet"
    readonly property string wallet_credit_card: "WalletCreditCard"
    readonly property string wallpaper: "Wallpaper"
    readonly property string wand: "Wand"
    readonly property string warning: "Warning"
    readonly property string warning_lock_open: "WarningLockOpen"
    readonly property string warning_shield: "WarningShield"
    readonly property string washer: "Washer"
    readonly property string water: "Water"
    readonly property string weather_blowing_snow: "WeatherBlowingSnow"
    readonly property string weather_cloudy: "WeatherCloudy"
    readonly property string weather_drizzle: "WeatherDrizzle"
    readonly property string weather_duststorm: "WeatherDuststorm"
    readonly property string weather_fog: "WeatherFog"
    readonly property string weather_hail_day: "WeatherHailDay"
    readonly property string weather_hail_night: "WeatherHailNight"
    readonly property string weather_haze: "WeatherHaze"
    readonly property string weather_moon: "WeatherMoon"
    readonly property string weather_moon_off: "WeatherMoonOff"
    readonly property string weather_partly_cloudy_day: "WeatherPartlyCloudyDay"
    readonly property string weather_partly_cloudy_night: "WeatherPartlyCloudyNight"
    readonly property string weather_rain: "WeatherRain"
    readonly property string weather_rain_showers_day: "WeatherRainShowersDay"
    readonly property string weather_rain_showers_night: "WeatherRainShowersNight"
    readonly property string weather_rain_snow: "WeatherRainSnow"
    readonly property string weather_snow: "WeatherSnow"
    readonly property string weather_snowflake: "WeatherSnowflake"
    readonly property string weather_snow_shower_day: "WeatherSnowShowerDay"
    readonly property string weather_snow_shower_night: "WeatherSnowShowerNight"
    readonly property string weather_squalls: "WeatherSqualls"
    readonly property string weather_sunny: "WeatherSunny"
    readonly property string weather_sunny_high: "WeatherSunnyHigh"
    readonly property string weather_sunny_low: "WeatherSunnyLow"
    readonly property string weather_thunderstorm: "WeatherThunderstorm"
    readonly property string web_asset: "WebAsset"
    readonly property string wheelchair_access: "WheelchairAccess"
    readonly property string whiteboard: "Whiteboard"
    readonly property string whiteboard_off: "WhiteboardOff"
    readonly property string wi_fi1: "WiFi1"
    readonly property string wi_fi2: "WiFi2"
    readonly property string wi_fi3: "WiFi3"
    readonly property string wi_fi4: "WiFi4"
    readonly property string wi_fi_lock: "WiFiLock"
    readonly property string wi_fi_off: "WiFiOff"
    readonly property string wi_fi_settings: "WiFiSettings"
    readonly property string wi_fi_warning: "WiFiWarning"
    readonly property string window: "Window"
    readonly property string window_ad: "WindowAd"
    readonly property string window_ad_off: "WindowAdOff"
    readonly property string window_ad_person: "WindowAdPerson"
    readonly property string window_apps: "WindowApps"
    readonly property string window_arrow_up: "WindowArrowUp"
    readonly property string window_brush: "WindowBrush"
    readonly property string window_bullet_list: "WindowBulletList"
    readonly property string window_bullet_list_add: "WindowBulletListAdd"
    readonly property string window_column_one_fourth_left: "WindowColumnOneFourthLeft"
    readonly property string window_console: "WindowConsole"
    readonly property string window_database: "WindowDatabase"
    readonly property string window_dev_edit: "WindowDevEdit"
    readonly property string window_dev_tools: "WindowDevTools"
    readonly property string window_edit: "WindowEdit"
    readonly property string window_fingerprint: "WindowFingerprint"
    readonly property string window_header_horizontal: "WindowHeaderHorizontal"
    readonly property string window_header_horizontal_off: "WindowHeaderHorizontalOff"
    readonly property string window_header_vertical: "WindowHeaderVertical"
    readonly property string window_in_private: "WindowInPrivate"
    readonly property string window_in_private_account: "WindowInPrivateAccount"
    readonly property string window_location_target: "WindowLocationTarget"
    readonly property string window_multiple: "WindowMultiple"
    readonly property string window_multiple_swap: "WindowMultipleSwap"
    readonly property string window_new: "WindowNew"
    readonly property string window_play: "WindowPlay"
    readonly property string window_settings: "WindowSettings"
    readonly property string window_shield: "WindowShield"
    readonly property string window_text: "WindowText"
    readonly property string window_wrench: "WindowWrench"
    readonly property string wrench: "Wrench"
    readonly property string wrench_screwdriver: "WrenchScrewdriver"
    readonly property string wrench_settings: "WrenchSettings"
    readonly property string xbox_console: "XboxConsole"
    readonly property string xbox_controller: "XboxController"
    readonly property string xbox_controller_error: "XboxControllerError"
    readonly property string xray: "Xray"
    readonly property string zoom_fit: "ZoomFit"
    readonly property string zoom_in: "ZoomIn"
    readonly property string zoom_out: "ZoomOut"
}
