SVS = SVS or {}

local lastCommandByPlayer = {}

local function senderOnlineID(player)
    return SVS.Util.playerOnlineID(player)
end

local function isValidVariant(entry, variantIndex)
    local index = tonumber(variantIndex)
    return index and index >= 1 and index <= #entry.variants
end

local function addZombieNoise(player, entry)
    if not SVS.Config.zombiesReactToShouts then return end
    local radius = tonumber(entry.noiseRadius) or 0
    if radius <= 0 then return end
    radius = math.min(radius, SVS.Config.server.maximumNoiseRadius or 30)

    if addSound then
        pcall(addSound,
            player,
            SVS.Util.safeCall(player, "getX", 0),
            SVS.Util.safeCall(player, "getY", 0),
            SVS.Util.safeCall(player, "getZ", 0),
            radius,
            radius
        )
    end
end

local function onClientCommand(module, command, player, args)
    if module ~= "SVS" or command ~= "play" then return end
    if not SVS.Config.multiplayer or not player or not args then return end

    local entry = SVS.GetManifestEntry(args.eventKey)
    if not entry or not isValidVariant(entry, args.variantIndex) then
        SVS.Util.debug("Rejected malformed voice command")
        return
    end

    local onlineID = senderOnlineID(player)
    if onlineID < 0 then return end

    local now = SVS.Util.nowMilliseconds()
    local previous = lastCommandByPlayer[onlineID] or 0
    if now - previous < (SVS.Config.server.minimumCommandIntervalMilliseconds or 1200) then
        SVS.Util.debug("Rate-limited voice command from " .. tostring(onlineID))
        return
    end
    lastCommandByPlayer[onlineID] = now

    local payload = {
        eventKey = args.eventKey,
        variantIndex = tonumber(args.variantIndex),
        onlineID = onlineID,
    }

    addZombieNoise(player, entry)

    if sendServerCommand then
        pcall(sendServerCommand, "SVS", "play", payload)
    end
end

SVS.Util.eventAdd("OnClientCommand", onClientCommand)
SVS.Util.log("Server module loaded, version " .. tostring(SVS.Version))
