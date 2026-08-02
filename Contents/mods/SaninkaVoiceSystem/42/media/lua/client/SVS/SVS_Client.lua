SVS = SVS or {}

local initialized = false

local function onCreatePlayer(playerIndex, player)
    SVS.Util.debug("Player created: " .. tostring(playerIndex))
end

local function onPlayerUpdate(player)
    if not player or not SVS.Util.isLocalPlayer(player) then return end
    SVS.ReactionEngine.update(player)
    SVS.Audio.updateQueue()
end

local function onServerCommand(module, command, args)
    if module ~= "SVS" then return end
    if command == "play" then
        SVS.Audio.receiveRemote(args)
    end
end

local function initialize()
    if initialized then return end
    initialized = true

    SVS.Util.eventAdd("OnCreatePlayer", onCreatePlayer)
    SVS.Util.eventAdd("OnPlayerUpdate", onPlayerUpdate)
    SVS.Util.eventAdd("OnServerCommand", onServerCommand)

    -- These names vary slightly between game builds. Missing events are skipped.
    SVS.Util.eventAdd("OnWeaponSwing", SVS.ReactionEngine.onWeaponSwing)
    SVS.Util.eventAdd("OnPlayerGetDamage", SVS.ReactionEngine.onPlayerDamage)
    SVS.Util.eventAdd("OnPlayerDeath", SVS.ReactionEngine.onPlayerDeath)
    SVS.Util.eventAdd("OnZombieDead", SVS.ReactionEngine.onZombieDead)

    SVS.Util.log("Client initialized, version " .. tostring(SVS.Version))
end

SVS.Util.eventAdd("OnGameStart", initialize)
SVS.Util.eventAdd("OnMainMenuEnter", function()
    SVS.Audio.clear()
    SVS.ReactionEngine.clear()
end)
