SVS = SVS or {}
SVS.Audio = SVS.Audio or {}

local stateByPlayer = {}
local pending = {}

local function playerKey(player)
    local onlineID = SVS.Util.playerOnlineID(player)
    if onlineID and onlineID >= 0 then return "online:" .. tostring(onlineID) end
    return "local:" .. tostring(SVS.Util.playerNumber(player))
end

local function getState(player)
    local key = playerKey(player)
    if not stateByPlayer[key] then
        stateByPlayer[key] = {
            lastGlobal = 0,
            lastCategory = {},
            lastEvent = {},
            lastVariant = {},
            busyUntil = 0,
        }
    end
    return stateByPlayer[key]
end

local function scaledCooldown(seconds)
    local multiplier = tonumber(SVS.Config.frequencyMultiplier) or 1
    if multiplier <= 0 then multiplier = 1 end
    return (seconds * 1000) / multiplier
end

local function categoryEnabled(entry)
    if not SVS.Config.enabled then return false end
    local enabled = SVS.Config.categories[entry.category]
    return enabled ~= false
end

local function canPlay(player, key, entry, options)
    options = options or {}
    if options.force then return true end
    if not categoryEnabled(entry) then return false end

    local now = SVS.Util.nowMilliseconds()
    local state = getState(player)

    if now < state.busyUntil then
        return false
    end

    if now - state.lastGlobal < scaledCooldown(SVS.Config.globalCooldown or 0) then
        return false
    end

    local categorySeconds = (SVS.Config.categoryCooldown and SVS.Config.categoryCooldown[entry.category]) or 0
    if now - (state.lastCategory[entry.category] or 0) < scaledCooldown(categorySeconds) then
        return false
    end

    if now - (state.lastEvent[key] or 0) < scaledCooldown(entry.cooldown or 0) then
        return false
    end

    return true
end

local function showSubtitle(player, text)
    if not SVS.Config.subtitles or not text or text == "" then return end

    if HaloTextHelper and HaloTextHelper.addText then
        local ok = pcall(HaloTextHelper.addText, player, text)
        if ok then return end
    end

    if player and player.setHaloNote then
        pcall(player.setHaloNote, player, text, 255, 255, 255, 300)
    end
end

local function playEmitterSound(player, soundName)
    if not player or not soundName then return false end

    local emitter = SVS.Util.safeCall(player, "getEmitter", nil)
    if emitter and emitter.playSound then
        local ok = pcall(emitter.playSound, emitter, soundName)
        if ok then return true end
    end

    if player.playSound then
        local ok = pcall(player.playSound, player, soundName)
        if ok then return true end
    end
    return false
end

local function rememberPlayback(player, key, entry, variantIndex)
    local now = SVS.Util.nowMilliseconds()
    local state = getState(player)
    state.lastGlobal = now
    state.lastCategory[entry.category] = now
    state.lastEvent[key] = now
    state.lastVariant[key] = variantIndex

    -- We cannot reliably query the clip duration before the real bank exists.
    -- A conservative lock prevents overlap and implements "do not interrupt".
    state.busyUntil = now + 1100
end

function SVS.Audio.playLocal(player, key, variantIndex, options)
    local entry = SVS.GetManifestEntry(key)
    if not entry or not player then return false end

    options = options or {}
    local state = getState(player)
    variantIndex = tonumber(variantIndex) or SVS.Util.randomIndex(#entry.variants, state.lastVariant[key])
    variantIndex = SVS.Util.clamp(variantIndex, 1, #entry.variants)
    local variant = entry.variants[variantIndex]

    if not options.remote and not canPlay(player, key, entry, options) then
        return false
    end

    local played = playEmitterSound(player, variant and variant.sound or nil)
    showSubtitle(player, variant and variant.subtitle or "")
    rememberPlayback(player, key, entry, variantIndex)

    if SVS.Config.debug.enabled then
        SVS.Util.log(string.format(
            "play key=%s variant=%d sound=%s remote=%s played=%s",
            tostring(key), variantIndex, tostring(variant and variant.sound),
            tostring(options.remote == true), tostring(played)
        ))
    end
    return true, variantIndex
end

function SVS.Audio.request(player, key, options)
    local entry = SVS.GetManifestEntry(key)
    if not entry or not player then return false end
    options = options or {}

    if not canPlay(player, key, entry, options) then
        return false
    end

    local state = getState(player)
    local variantIndex = options.variantIndex or SVS.Util.randomIndex(#entry.variants, state.lastVariant[key])
    local played = SVS.Audio.playLocal(player, key, variantIndex, options)
    if not played then return false end

    if SVS.Config.multiplayer and isClient and isClient() and sendClientCommand then
        local args = {
            eventKey = key,
            variantIndex = variantIndex,
            onlineID = SVS.Util.playerOnlineID(player),
        }
        pcall(sendClientCommand, "SVS", "play", args)
    end
    return true
end

function SVS.Audio.enqueue(player, key, options)
    local entry = SVS.GetManifestEntry(key)
    if not entry or not player then return false end

    table.insert(pending, {
        player = player,
        key = key,
        options = options or {},
        priority = tonumber(entry.priority) or 0,
        queuedAt = SVS.Util.nowMilliseconds(),
    })
    table.sort(pending, function(a, b)
        if a.priority == b.priority then return a.queuedAt < b.queuedAt end
        return a.priority > b.priority
    end)
    return true
end

function SVS.Audio.updateQueue()
    if #pending == 0 then return end

    for index, item in ipairs(pending) do
        if item.player and SVS.Audio.request(item.player, item.key, item.options) then
            table.remove(pending, index)
            return
        end
        if SVS.Util.nowMilliseconds() - item.queuedAt > 15000 then
            table.remove(pending, index)
            return
        end
    end
end

function SVS.Audio.receiveRemote(args)
    if not args or not args.eventKey or not SVS.IsKnownEvent(args.eventKey) then return end
    if not getPlayerByOnlineID then return end

    local onlineID = tonumber(args.onlineID)
    if not onlineID or onlineID < 0 then return end

    local localPlayer = getPlayer and getPlayer() or nil
    if localPlayer and SVS.Util.playerOnlineID(localPlayer) == onlineID then
        return
    end

    local remotePlayer = getPlayerByOnlineID(onlineID)
    if not remotePlayer then return end

    SVS.Audio.playLocal(remotePlayer, args.eventKey, args.variantIndex, {
        remote = true,
        force = true,
    })
end

function SVS.Audio.clear()
    stateByPlayer = {}
    pending = {}
end
