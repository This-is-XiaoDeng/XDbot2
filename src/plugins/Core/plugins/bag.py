import json
import traceback
from . import _error
from . import _lang
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.exception import FinishedException
from nonebot.params import CommandArg

from . import _userCtrl

bag = on_command("bag", aliases={"背包"})
ctrlGroup = json.load(open("data/ctrl.json", encoding="utf-8"))["control"]


@bag.handle()
async def bagHandle(
    bot: Bot, event: GroupMessageEvent, message: Message = CommandArg()
):
    try:
        argument = message.extract_plain_text().splitlines()
        if argument == []:
            argument = [""]
        else:
            argument = argument[0].split(" ")
        bagData = json.load(open("data/etm.bag.json", encoding="utf-8"))
        itemData = json.load(open("data/etm.items.json", encoding="utf-8"))
        if argument[0] == "":
            text = _lang.text(
                "bag.get",
                [
                    (await bot.get_stranger_info(user_id=event.get_user_id()))[
                        "nickname"
                    ]
                ],
                event.get_user_id(),
            )
            length = 0
            for item in bagData[event.get_user_id()]:
                name = item["data"]["displayName"] or itemData[item["id"]]["name"]
                text += f" {length}. {name} x{item['count']}\n"
                length += 1
            await bag.finish(text)
        elif argument[0] == "view" or argument[0] == "看看":
            item = bagData[event.get_user_id()][int(argument[1])]
            name = item["data"]["displayName"] or itemData[item["id"]]["name"]
            info = item["data"]["information"] or itemData[item["id"]]["info"]
            await bag.finish(
                _lang.text(
                    "bag.item",
                    [name, item["count"], info],
                    event.get_user_id(),
                )
            )
        elif argument[0] == "drop" or argument[0] == "丢弃":
            try:
                _userCtrl.removeItemsFromBag(
                    userID=event.get_user_id(),
                    itemPos=int(argument[1]),
                    count=bagData[event.get_user_id()][int(
                        argument[1])]["count"],
                    removeType="Drop",
                )
            except _userCtrl.ItemCanNotRemove:
                await bag.finish(_lang.text("bag.cannot_drop", [], event.get_user_id()))
            await bag.finish(_lang.text("bag.finish", [], event.get_user_id()))
        elif argument[0] in ["edit", "编辑"]:
            item = bagData[event.get_user_id()][int(argument[1])]
            if item["id"] == "4":
                if not item["data"]["saved"]:
                    try:
                        _userCtrl.removeItemsFromBag(
                            event.get_user_id(), int(
                                argument[1]), 1, "Use")
                    except _userCtrl.ItemCanNotRemove:
                        await bag.finish(_lang.text("bag.cannot_use", [], event.get_user_id()))
                    item["data"]["text"] = "\n".join(
                        str(message).split("\n")[1:])
                    _userCtrl.addItem(
                        event.get_user_id(), "4", 1, item["data"])
                    await bag.finish(_lang.text("bag.finish", [], event.get_user_id()))
                else:
                    await bag.finish(_lang.text("bag.book_saved", [], event.get_user_id()))
            else:
                await bag.finish(_lang.text("bag.notfound", [], event.get_user_id()))
        elif argument[0] in ["save", "保存"]:
            item = bagData[event.get_user_id()][int(argument[1])]
            if item["id"] == "4":
                if not item["data"]["saved"]:
                    try:
                        _userCtrl.removeItemsFromBag(
                            event.get_user_id(), int(
                                argument[1]), 1, "Use")
                    except _userCtrl.ItemCanNotRemove:
                        await bag.finish(_lang.text("bag.cannot_use", [], event.get_user_id()))
                    item["data"]["saved"] = True
                    item["data"]["author"] = (await bot.get_stranger_info(user_id=event.get_user_id()))["nickname"]
                    _userCtrl.addItem(
                        event.get_user_id(), "4", 1, item["data"])
                    await bag.finish(_lang.text("bag.finish"))
                else:
                    await bag.finish(_lang.text("bag.book_saved", [], event.get_user_id()))
        elif argument[0] in ["rename", "重命名"]:
            _userCtrl.removeItemsByID(event.get_user_id(), "5", 1, )
            bagData[event.get_user_id()][int(argument[1])]["data"]["displayName"] = argument[2]
            if len(str(message).splitlines()) >= 2:
                bagData[event.get_user_id()][int(argument[1])]["data"]["information"] = "\n".join(message.splielines()[1:])
            json.dump(bagData, open("data/etm.bag.json", "w"))
            

    except FinishedException:
        raise FinishedException()
    except KeyError:
        await bag.finish(_lang.text("bag.empty", [], event.get_user_id()))
    except IndexError:
        await bag.finish(_lang.text("bag.notfound", [], event.get_user_id()))
    except Exception:
        await _error.report(traceback.format_exc(), bag)


# [HELPSTART] Version: 2
# Command: bag
# Info: 查看背包，并对背包中的物品进行操作
# Msg: 背包操作
# Usage: bag：查看背包中的所有物品
# Usage: bag view <背包物品ID>：查看<背包物品ID>的详细信息
# Usage: bag drop <背包物品ID>：丢弃<背包物品ID>（如果可以）
# [HELPEND]
