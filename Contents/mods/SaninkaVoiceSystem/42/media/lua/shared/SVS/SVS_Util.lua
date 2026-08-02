SVS = SVS or {}
SVS.Util = SVS.Util or {}

function SVS.Util.nowMilliseconds()
    if getTimestampMs then
        local ok, value = pcall(getTimestampMs)
        if ok and value then return value end
    end
    return os.time() * 1000
end

function SVS.Util.log(message)
    print("[SVS] " .. tostring(message))
end

function SVS.Util.debug(message)
    if SVS.Config and SVS.Config.debug and SVS.Config.debug.enabled then
        SVS.Util.log(message)
    end
end

function SVS.Util.safeCall(object, methodName, fallback, ...)
    if object == nil then return fallback end

    local okMethod, method = pcall(function()
        return object[methodName]
    end)
    if not okMethod or type(method) ~= "function" then
        return fallback
    end

    local ok, value = pcall(method, object, ...)
    if not ok or value == nil then
        return fallback
    end
    return value
end

function SVS.Util.clamp(value, minimum, maximum)
    if value < minimum then return minimum end
    if value > maximum then return maximum end
    return value
end

function SVS.Util.distanceSquared(a, b)
    if not a or not b then return math.huge end
    local ax = SVS.Util.safeCall(a, "getX", 0)
    local ay = SVS.Util.safeCall(a, "getY", 0)
    local bx = SVS.Util.safeCall(b, "getX", 0)
    local by = SVS.Util.safeCall(b, "getY", 0)
    local dx = ax - bx
    local dy = ay - by
    return dx * dx + dy * dy
end

function SVS.Util.isLocalPlayer(player)
    if not player then return false end
    if not getPlayer then return true end
    local ok, localPlayer = pcall(getPlayer)
    return ok and localPlayer == player
end

function SVS.Util.playerOnlineID(player)
    return SVS.Util.safeCall(player, "getOnlineID", -1)
end

function SVS.Util.playerNumber(player)
    return SVS.Util.safeCall(player, "getPlayerNum", 0)
end

function SVS.Util.randomIndex(count, previous)
    if not count or count <= 1 then return 1 end
    local index = ZombRand and (ZombRand(count) + 1) or math.random(count)
    if previous and index == previous then
        index = (index % count) + 1
    end
    return index
end

function SVS.Util.eventAdd(name, callback)
    if not Events then return false end
    local event = Events[name]
    if event and event.Add then
        event.Add(callback)
        SVS.Util.debug("Registered event: " .. tostring(name))
        return true
    end
    SVS.Util.debug("Skipped unavailable event: " .. tostring(name))
    return false
end

function SVS.Util.tableContains(list, value)
    if not list then return false end
    for _, item in ipairs(list) do
        if item == value then return true end
    end
    return false
end
