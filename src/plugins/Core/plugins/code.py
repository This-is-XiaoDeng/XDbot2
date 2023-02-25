import traceback
import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import ActionFailed, Bot, Message, GroupMessageEvent
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
import json
from . import _error
from . import _lang
import asyncio

code = on_command("code", aliases={"运行代码"})
header = {
    "Authorization": "Token a238bd14-14ae-43e4-a7ea-8942edd9b98c",
    "Content-Type": "application/json"
}
file_types = {
    "python": ".py",
    "cpp": ".cpp",
    "c": ".c",
    "bash": ".sh",
    "rust": ".rs",
    "java": ".java"
}


async def run_code(message: Message):
    # 收集信息
    arguments = str(message).split("\n")[0].strip().split(" ")
    language = arguments[0]
    if len(arguments) > 3:
        stdin = arguments[-1]
    else:
        stdin = ""
    if language in file_types.keys():
        file_type = file_types[language]
    else:
        file_type = ""
    src = "\n".join(str(message).split("\n")[1:])
    # 请求数据
    request_data = {
        "files": [
            {
                "name": f"main{file_type}",
                "content": src
            }
        ],
        "stdin": stdin
    }
    # 发送请求
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"https://glot.io/api/run/{language}/latest",
            headers=header,
            data=json.dumps(request_data)
        )
    data = json.loads(response.read())
    # 分析数据
    if "message" in data.keys():
        return data["message"]
    elif data["stderr"]:
        return data["stderr"]
    elif data["error"]:
        return data["error"]
    else:
        return data["stdout"]


@code.handle()
async def code_handler(bot: Bot, event: GroupMessageEvent, message: Message = CommandArg()):
    try:
        reply_message = event.message_id
        try:
            message_id = (await bot.send_group_msg(
                message=Message((
                    f"[CQ:reply,id={reply_message}]{await run_code(message)}\n"
                    f"{_lang.text('code.delete_warning', [], str(event.user_id))}")),
                group_id=event.group_id))["message_id"]
        except ActionFailed:
            await code.finish(_lang.text("code.too_long", [], str(event.user_id)))
        await asyncio.sleep(60)
        await bot.delete_msg(message_id=message_id)
    except FinishedException:
        raise FinishedException()
    except BaseException:
        await _error.report(traceback.format_exc(), code)