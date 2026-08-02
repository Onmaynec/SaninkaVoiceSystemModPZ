SVS = SVS or {}
SVS.ReactionEngine = SVS.ReactionEngine or {}

local playerStates = {}

local function getPlayerState(player)
    local key = SVS.Util.playerNumber(player)
    if not playerStates[key] then
        playerStates[key] = {
            lastStatsPoll = 0,
            lastWorldPoll = 0,
            lastActionPoll = 0,
            levels = {},
            lastActionIdentity = nil,
            zombieLevel = 0,
            dangerSeenAt = 0,
            wasNight = false,
            badWeather = false,
            bitten = false,
            bleeding = false,
        }
    end
    return playerStates[key]
end

local function queue(player, key)
    if key and SVS.IsKnownEvent(key) then
        SVS.Audio.enqueue(player, key)
    end
end

local function severity(value, light, heavy)
    if value >= heavy then return 2 end
    if value >= light then return 1 end
    return 0
end

local function triggerChangedLevel(player, state, name, level, lightKey, heavyKey)
    local previous = state.levels[name] or 0
    state.levels[name] = level
    if level <= previous then return end
    if level >= 2 then
        queue(player, heavyKey)
    elseif level == 1 then
        queue(player, lightKey)
    end
end

local function bodyPartBitten(bodyDamage)
    local parts = SVS.Util.safeCall(bodyDamage, "getBodyParts", nil)
    if not parts or not parts.size then return false end
    local count = SVS.Util.safeCall(parts, "size", 0)
    for index = 0, count - 1 do
        local part = SVS.Util.safeCall(parts, "get", nil, index)
        if part then
            local bitten = SVS.Util.safeCall(part, "bitten", false)
            if not bitten then bitten = SVS.Util.safeCall(part, "isBitten", false) end
            if bitten then return true end
        end
    end
    return false
end

local function pollStats(player, state)
    local stats = SVS.Util.safeCall(player, "getStats", nil)
    local body = SVS.Util.safeCall(player, "getBodyDamage", nil)
    if not stats or not body then return end

    local t = SVS.Config.thresholds

    triggerChangedLevel(player, state, "hunger",
        severity(SVS.Util.safeCall(stats, "getHunger", 0), t.hungerLight, t.hungerHeavy),
        "hunger_light", "hunger_heavy")

    triggerChangedLevel(player, state, "thirst",
        severity(SVS.Util.safeCall(stats, "getThirst", 0), t.thirstLight, t.thirstHeavy),
        "thirst_light", "thirst_heavy")

    triggerChangedLevel(player, state, "fatigue",
        severity(SVS.Util.safeCall(stats, "getFatigue", 0), t.fatigueLight, t.fatigueHeavy),
        "fatigue_light", "fatigue_heavy")

    triggerChangedLevel(player, state, "pain",
        severity(SVS.Util.safeCall(stats, "getPain", 0), t.painLight, t.painHeavy),
        "pain_light", "pain_heavy")

    triggerChangedLevel(player, state, "panic",
        severity(SVS.Util.safeCall(stats, "getPanic", 0), t.panicLight, t.panicHeavy),
        "panic_light", "panic_heavy")

    local boredom = SVS.Util.safeCall(stats, "getBoredom", 0)
    triggerChangedLevel(player, state, "boredom", boredom >= t.boredom and 1 or 0,
        "boredom", "boredom")

    local unhappiness = SVS.Util.safeCall(body, "getUnhappynessLevel", nil)
    if unhappiness == nil then unhappiness = SVS.Util.safeCall(stats, "getUnhappyness", 0) end
    triggerChangedLevel(player, state, "sadness", unhappiness >= t.sadness and 1 or 0,
        "sadness", "sadness")

    local temperature = SVS.Util.safeCall(body, "getTemperature", 37)
    local temperatureLevel = temperature >= t.heat and 2 or (temperature <= t.cold and 1 or 0)
    local previousTemperature = state.levels.temperature or 0
    state.levels.temperature = temperatureLevel
    if temperatureLevel ~= previousTemperature then
        if temperatureLevel == 2 then queue(player, "heat") end
        if temperatureLevel == 1 then queue(player, "cold") end
    end

    local weight = SVS.Util.safeCall(player, "getInventoryWeight", nil)
    if weight == nil then
        local inventory = SVS.Util.safeCall(player, "getInventory", nil)
        weight = SVS.Util.safeCall(inventory, "getCapacityWeight", 0)
    end
    local maxWeight = math.max(1, SVS.Util.safeCall(player, "getMaxWeight", 1))
    triggerChangedLevel(player, state, "encumbered",
        severity(weight / maxWeight, t.encumberedLight, t.encumberedHeavy),
        "encumbered_light", "encumbered_heavy")

    local sickness = math.max(
        SVS.Util.safeCall(body, "getFoodSicknessLevel", 0),
        SVS.Util.safeCall(body, "getPoisonLevel", 0)
    )
    triggerChangedLevel(player, state, "sickness",
        severity(sickness, t.sicknessLight, t.sicknessHeavy),
        "sickness_light", "sickness_heavy")

    local bleeding = SVS.Util.safeCall(body, "IsBleeding", false)
    if not bleeding then bleeding = SVS.Util.safeCall(body, "isBleeding", false) end
    if bleeding and not state.bleeding then queue(player, "bleeding") end
    state.bleeding = bleeding

    local bitten = bodyPartBitten(body)
    if bitten and not state.bitten then queue(player, "bitten") end
    state.bitten = bitten
end

local function nearbyZombieCount(player)
    local cell = SVS.Util.safeCall(player, "getCell", nil)
    local zombies = SVS.Util.safeCall(cell, "getZombieList", nil)
    if not zombies then return 0 end

    local radius = SVS.Config.thresholds.zombieRadius
    local radiusSquared = radius * radius
    local count = 0
    local size = SVS.Util.safeCall(zombies, "size", 0)
    for index = 0, size - 1 do
        local zombie = SVS.Util.safeCall(zombies, "get", nil, index)
        if zombie and SVS.Util.distanceSquared(player, zombie) <= radiusSquared then
            count = count + 1
            if count >= SVS.Config.thresholds.zombieHorde then break end
        end
    end
    return count
end

local function getHour()
    if not getGameTime then return 12 end
    local time = getGameTime()
    return SVS.Util.safeCall(time, "getHour", 12)
end

local function hasBadWeather()
    if not getClimateManager then return false end
    local climate = getClimateManager()
    local rain = SVS.Util.safeCall(climate, "getPrecipitationIntensity", 0)
    local fog = SVS.Util.safeCall(climate, "getFogIntensity", 0)
    return rain >= 0.55 or fog >= 0.65
end

local function pollWorld(player, state)
    local count = nearbyZombieCount(player)
    local t = SVS.Config.thresholds
    local level = count >= t.zombieHorde and 3 or (count >= t.zombieMedium and 2 or (count > 0 and 1 or 0))

    if level > state.zombieLevel then
        if level == 3 then queue(player, "zombie_spotted_horde")
        elseif level == 2 then queue(player, "zombie_spotted_medium")
        else queue(player, "zombie_spotted_small") end
    elseif level == 0 and state.zombieLevel > 0 then
        local now = SVS.Util.nowMilliseconds()
        if now - state.dangerSeenAt >= 12000 then
            queue(player, "safe_relief")
        end
    end

    if level > 0 then state.dangerSeenAt = SVS.Util.nowMilliseconds() end
    state.zombieLevel = level

    local hour = getHour()
    local night = hour >= 20 or hour < 5
    if night and not state.wasNight then queue(player, "night_started") end
    state.wasNight = night

    local badWeather = hasBadWeather()
    if badWeather and not state.badWeather then queue(player, "weather_bad") end
    state.badWeather = badWeather
end

local actionMap = {
    Reload = "reload_start",
    Bandage = "treatment_start",
    Medical = "treatment_start",
    Disinfect = "treatment_start",
    Stitch = "treatment_start",
    Read = "reading_start",
    VehicleMechanics = "vehicle_repair",
    Fix = "vehicle_repair",
    Build = "build_start",
    Craft = "craft_start",
    EnterVehicle = "enter_vehicle",
    Cook = "cooking_start",
    OpenDoor = "door_locked",
    Break = "door_breaking",
}

local function currentTimedAction(player)
    if not ISTimedActionQueue or not ISTimedActionQueue.getTimedActionQueue then return nil end
    local ok, queueObject = pcall(ISTimedActionQueue.getTimedActionQueue, player)
    if not ok or not queueObject or not queueObject.queue then return nil end
    return queueObject.queue[1]
end

local function actionName(action)
    if not action then return "" end
    if action.Type then return tostring(action.Type) end
    if action.type then return tostring(action.type) end
    return tostring(action)
end

local function pollTimedAction(player, state)
    local action = currentTimedAction(player)
    if not action then
        state.lastActionIdentity = nil
        return
    end

    local identity = tostring(action)
    if identity == state.lastActionIdentity then return end
    state.lastActionIdentity = identity

    local name = actionName(action)
    for needle, key in pairs(actionMap) do
        if string.find(name, needle, 1, true) then
            queue(player, key)
            return
        end
    end
end

function SVS.ReactionEngine.update(player)
    if not player or not SVS.Config.enabled then return end
    local state = getPlayerState(player)
    local now = SVS.Util.nowMilliseconds()

    if now - state.lastStatsPoll >= SVS.Config.polling.statsMilliseconds then
        state.lastStatsPoll = now
        pollStats(player, state)
    end

    if now - state.lastWorldPoll >= SVS.Config.polling.worldMilliseconds then
        state.lastWorldPoll = now
        pollWorld(player, state)
    end

    if now - state.lastActionPoll >= SVS.Config.polling.timedActionMilliseconds then
        state.lastActionPoll = now
        pollTimedAction(player, state)
    end
end

function SVS.ReactionEngine.onWeaponSwing(character, weapon)
    if not character or not SVS.Util.isLocalPlayer(character) then return end
    local weight = SVS.Util.safeCall(weapon, "getWeight", 0)
    queue(character, weight >= 2.5 and "combat_swing_heavy" or "combat_swing_light")
end

function SVS.ReactionEngine.onPlayerDamage(player, damageType, damage)
    if not player or not SVS.Util.isLocalPlayer(player) then return end
    local amount = tonumber(damage) or 0
    if amount >= 20 then queue(player, "combat_hit_taken_heavy")
    elseif amount >= 7 then queue(player, "combat_hit_taken_medium")
    else queue(player, "combat_hit_taken_light") end
end

function SVS.ReactionEngine.onPlayerDeath(player)
    if player and SVS.Util.isLocalPlayer(player) then
        SVS.Audio.request(player, "combat_death", { force = true })
    end
end

function SVS.ReactionEngine.onZombieDead(zombie)
    local player = getPlayer and getPlayer() or nil
    if player and zombie and SVS.Util.distanceSquared(player, zombie) <= 16 then
        queue(player, "zombie_killed")
    end
end

function SVS.ReactionEngine.clear()
    playerStates = {}
end
