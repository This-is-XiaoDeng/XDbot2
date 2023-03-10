import json
import traceback
import random
import time
from . import _error
from . import _lang
from nonebot import on_keyword, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
from . import _userCtrl

sign = on_keyword({"sign", "签到"})
signrank = on_command("sign", aliases={"签到"})
ctrlGroup = json.load(open("data/ctrl.json", encoding="utf-8"))["control"]
time_to_next_day_format = "%H:%M'%S''"  # 下次可签到时间输出格式，你要是看着不顺眼在这里改


@signrank.handle()
async def signrankHandle(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
):
    time_to_next_day = time.strftime(
        time_to_next_day_format,
        time.gmtime(int((int(time.time() / 86400) + 1) * 86400 - time.time())),
    )
    args = args.extract_plain_text().split(" ")
    if not args[0] == "rank":
        return
    rank = _lang.text(
        "sign.rank_title",
        [time_to_next_day],
        event.get_user_id())
    try:
        with open("data/sign.rank.json", "r") as f:
            sign_rank_data = json.load(f)
            if sign_rank_data["day"] != int(time.time() / 86400):
                raise FileNotFoundError
    except BaseException:
        sign_rank_data = {"day": int(time.time() / 86400), "rank": []}
    if not sign_rank_data["rank"]:
        await signrank.finish(_lang.text("sign.rank_empty", [], event.get_user_id()))
    num = 0
    me = _lang.text("sign.rank_me", [], event.get_user_id())
    for i in sign_rank_data["rank"]:
        num += 1
        rank += f"{str(num)}. {(await bot.get_stranger_info(user_id=i['qq']))['nickname']}（{i['time']}）\n"
        if i["qq"] == int(event.get_user_id()):
            me = f"{str(num)}. {(await bot.get_stranger_info(user_id=i['qq']))['nickname']}（{i['time']}）"
    rank += "--------------------\n" + me
    await signrank.finish(rank)


@sign.handle()
async def signHandle(bot: Bot, event: GroupMessageEvent):
    time_to_next_day = time.strftime(
        time_to_next_day_format,
        time.gmtime(int((int(time.time() / 86400) + 1) * 86400 - time.time())),
    )
    try:
        if event.get_plaintext().__len__() <= 5:
            latestSign = json.load(
                open(
                    "data/sign.latestTime.json",
                    encoding="utf-8"))
            signDay = json.load(
                open(
                    "data/sign.signDay.json",
                    encoding="utf-8"))
            userData = json.load(
                open(
                    "data/etm.userData.json",
                    encoding="utf-8"))
            userID = event.get_user_id()
            # 检查数据是否存在
            if userID not in list(latestSign.keys()):
                latestSign[userID] = 0
            if userID not in list(signDay.keys()):
                signDay[userID] = 0
            if userID not in list(userData.keys()):
                userData[userID] = {
                    "level": 1,
                    "exp": 0,
                    "vip": {"endTime": None, "level": None},
                }
            # 修改数据
            if latestSign[userID] == int(time.time() / 86400):
                await sign.finish(
                    _lang.text(
                        "sign.cannot",
                        [time_to_next_day],
                        event.get_user_id()),
                    at_sender=True,
                )
            if latestSign[userID] - int(time.time() / 86400) == -1:
                signDay[userID] += 1
            else:
                signDay[userID] = 0
            latestSign[userID] = int(time.time() / 86400)
            # 基础随机奖励
            addCoin = random.randint(0, 15)
            addExp = random.randint(1, 10)
            # 连续签到加成
            addCoin *= 1 + signDay[userID] / 100
            addExp *= 1 + signDay[userID] / 100
            # 等级加成
            addCoin *= 1 + userData[userID]["level"] / 2 / 10
            addExp *= 1 + userData[userID]["level"] / 2 / 10
            # VIP加成
            if userData[userID]["vip"]["level"]:
                addCoin *= 1 + userData[userID]["vip"]["level"] / 2
                addExp *= 1 + userData[userID]["vip"]["level"] / 2
            # 实际收入
            addCoin /= 2
            addExp /= 1.5
            addCoin = int(addCoin)
            addExp = int(addExp)
            # 修改数据
            oldCoinCount = _userCtrl.getCountOfItem(userID, "0")
            _userCtrl.addItem(userID, "0", addCoin, dict())
            _userCtrl.addExp(userID, addExp)
            # 保存数据
            json.dump(
                signDay,
                open(
                    "data/sign.signDay.json",
                    "w",
                    encoding="utf-8"))
            json.dump(
                latestSign, open(
                    "data/sign.latestTime.json", "w", encoding="utf-8")
            )
            try:
                with open("data/sign.rank.json", "r") as f:
                    sign_rank_data = json.load(f)
                    if sign_rank_data["day"] != int(time.time() / 86400):
                        raise FileNotFoundError
            except BaseException:
                sign_rank_data = {"day": int(time.time() / 86400), "rank": []}
            sign_rank_data["rank"].append(
                {
                    "qq": int(event.get_user_id()),
                    "time": time.strftime("%H:%M:%S", time.localtime()),
                }
            )
            with open("data/sign.rank.json", "w") as f:
                json.dump(sign_rank_data, f)
            # 反馈结果
            await sign.finish(
                f"""+-----------------------------+
\t{_lang.text('sign.success',[],event.get_user_id())}
 「VimCoin」：{oldCoinCount} -> {oldCoinCount + addCoin} (+{addCoin})
 「{_lang.text('sign.exp',[],event.get_user_id())}」：{userData[userID]['exp']} -> {userData[userID]['exp'] + addExp} (+{addExp})
    {_lang.text("sign.days",[signDay[userID]],event.get_user_id())}
    {_lang.text("sign.count",[len(sign_rank_data['rank'])],event.get_user_id())}
+-----------------------------+"""
            )

    except FinishedException:
        raise FinishedException()
    except Exception:
        await _error.report(traceback.format_exc(), sign)


# [HELPSTART]
# !Usage 1 sign
# !Info 1 在 XDbot2 上签到
# [HELPEND]
