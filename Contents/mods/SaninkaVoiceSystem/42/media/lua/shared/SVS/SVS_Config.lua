SVS = SVS or {}

SVS.Version = "0.1.0-alpha"

SVS.Config = {
    enabled = true,
    subtitles = true,
    multiplayer = true,
    zombiesReactToShouts = true,

    -- 0.50 = fewer reactions, 1.00 = normal, 1.50 = more reactions.
    frequencyMultiplier = 1.00,

    globalCooldown = 7,
    categoryCooldown = {
        native = 1,
        breathing = 8,
        combat = 1,
        body = 8,
        danger = 20,
        world = 120,
        actions = 20,
        conditions = 120,
        multiplayer = 2,
    },

    categories = {
        native = true,
        breathing = true,
        combat = true,
        body = true,
        danger = true,
        world = true,
        actions = true,
        conditions = true,
        multiplayer = true,
    },

    thresholds = {
        hungerLight = 0.35,
        hungerHeavy = 0.70,
        thirstLight = 0.35,
        thirstHeavy = 0.70,
        fatigueLight = 0.50,
        fatigueHeavy = 0.80,
        painLight = 25,
        painHeavy = 60,
        panicLight = 25,
        panicHeavy = 70,
        boredom = 50,
        sadness = 50,
        heat = 38.5,
        cold = 35.5,
        encumberedLight = 0.90,
        encumberedHeavy = 1.15,
        sicknessLight = 20,
        sicknessHeavy = 60,
        zombieMedium = 4,
        zombieHorde = 10,
        zombieRadius = 12,
    },

    polling = {
        statsMilliseconds = 1100,
        worldMilliseconds = 2500,
        timedActionMilliseconds = 500,
    },

    server = {
        minimumCommandIntervalMilliseconds = 1200,
        maximumNoiseRadius = 30,
    },

    debug = {
        enabled = false,
        verbose = false,
    },
}

function SVS.GetConfig()
    return SVS.Config
end
