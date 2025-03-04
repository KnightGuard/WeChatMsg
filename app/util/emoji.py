# -*- coding: utf-8 -*-
"""
emoji.py

!!!声明：
由于表情包并不属于个人，并且其可能具有版权风险，你只有浏览权没有拥有权
另外访问腾讯API可能会给腾讯服务器造成压力
所以禁止任何人以任何方式修改或间接修改该文件，违者后果自负
"""

import os
import traceback
import xml.etree.ElementTree as ET

import requests

from app.log import log, logger

root_path = './data/emoji/'
if not os.path.exists('./data'):
    os.mkdir('./data')
if not os.path.exists(root_path):
    os.mkdir(root_path)

@log
def get_image_format(header):
    # 定义图片格式的 magic numbers
    image_formats = {
        b'\xFF\xD8\xFF': 'jpeg',
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': 'png',
        b'\x47\x49\x46': 'gif',
        b'\x42\x4D': 'bmp',
        # 添加其他图片格式的 magic numbers
    }
    # 判断文件的图片格式
    for magic_number, image_format in image_formats.items():
        if header.startswith(magic_number):
            return image_format
    # 如果无法识别格式，返回 None
    return None

@log
def parser_xml(xml_string):
    assert type(xml_string) == str
    # Parse the XML string
    root = ET.fromstring(xml_string)
    emoji = root.find('./emoji')
    # Accessing attributes of the 'emoji' element
    fromusername = emoji.get('fromusername')
    tousername = emoji.get('tousername')
    md5 = emoji.get('md5')
    cdnurl = emoji.get('cdnurl')
    encrypturl = emoji.get('encrypturl')
    thumburl = emoji.get('thumburl')
    externurl = emoji.get('externurl')
    androidmd5 = emoji.get('androidmd5')
    width = emoji.get('width')
    height = emoji.get('height')
    return {
        'width': width,
        'height': height,
        'cdnurl': cdnurl,
        'thumburl': thumburl if thumburl else cdnurl,
        'md5': md5 if md5 else androidmd5,
    }

@log
def download(url, output_dir, name, thumb=False):
    if not url:
        return ':/icons/icons/404.png'
    resp = requests.get(url)
    byte = resp.content
    image_format = get_image_format(byte[:8])
    if image_format:
        if thumb:
            output_path = os.path.join(output_dir, 'th_' + name + '.' + image_format)
        else:
            output_path = os.path.join(output_dir, name + '.' + image_format)
    else:
        output_path = os.path.join(output_dir, name)
    with open(output_path, 'wb') as f:
        f.write(resp.content)
    return output_path


def get_emoji(xml_string, thumb=True, output_path=root_path) -> str:
    try:
        emoji_info = parser_xml(xml_string)
        md5 = emoji_info['md5']
        image_format = ['.png', '.gif', '.jpeg']
        for f in image_format:
            prefix = 'th_' if thumb else ''
            file_path = os.path.join(output_path, prefix + md5 + f)
            if os.path.exists(file_path):
                print('表情包已存在')
                return file_path
        url = emoji_info['thumburl'] if thumb else emoji_info['cdnurl']
        print("下载表情包ing:", url)
        emoji_path = download(url, output_path, md5, thumb)
        return emoji_path
    except:
        logger.error(traceback.format_exc())
        return ""


if __name__ == '__main__':
    xml_string = '<msg><emoji fromusername = "wxid_0o18ef858vnu22" tousername = "wxid_27hqbq7vx5hf22" type="2" idbuffer="media:0_0" md5="71ce49ed3ce9e57e43e07f802983bf45" len = "352588" productid="com.tencent.xin.emoticon.person.stiker_1678703862259eb01f2ef4a313" androidmd5="71ce49ed3ce9e57e43e07f802983bf45" androidlen="352588" s60v3md5 = "71ce49ed3ce9e57e43e07f802983bf45" s60v3len="352588" s60v5md5 = "71ce49ed3ce9e57e43e07f802983bf45" s60v5len="352588" cdnurl = "http://wxapp.tc.qq.com/262/20304/stodownload?m=71ce49ed3ce9e57e43e07f802983bf45&amp;filekey=30350201010421301f020201060402535a041071ce49ed3ce9e57e43e07f802983bf45020305614c040d00000004627466730000000132&amp;hy=SZ&amp;storeid=263ffa00b000720d03274c5820000010600004f50535a1ca0c950b64287022&amp;bizid=1023" designerid = "" thumburl = "http://mmbiz.qpic.cn/mmemoticon/ajNVdqHZLLDSKTMRgM8agiadpFhKz9IJ3cD5Ra2sTROibOaShdt3D4z6PfE92WkjQY/0" encrypturl = "http://wxapp.tc.qq.com/262/20304/stodownload?m=cbaae1d847aac6389652b65562bacaa2&amp;filekey=30350201010421301f020201060402535a0410cbaae1d847aac6389652b65562bacaa20203056150040d00000004627466730000000132&amp;hy=SZ&amp;storeid=263ffa00b0008d8223274c5820000010600004f50535a17b82910b64764739&amp;bizid=1023" aeskey= "7051ab2a34442dec63434832463f45ce" externurl = "http://wxapp.tc.qq.com/262/20304/stodownload?m=960f68693454dfa64b9966ca5d70dbd3&amp;filekey=30340201010420301e020201060402535a0410960f68693454dfa64b9966ca5d70dbd3020221a0040d00000004627466730000000132&amp;hy=SZ&amp;storeid=26423dbe3000793a8720e40de0000010600004f50535a1d40c950b71be0a50&amp;bizid=1023" externmd5 = "41895664fc5a77878e2155fc96209a19" width= "240" height= "240" tpurl= "" tpauthkey= "" attachedtext= "" attachedtextcolor= "" lensid= "" emojiattr= "" linkid= "" desc= "ChEKB2RlZmF1bHQSBuWNlee6rw==" ></emoji> </msg>'
    res1 = parser_xml(xml_string)
    print(res1, res1['md5'])
    # download(res1['cdnurl'], "./data/emoji/", res1['md5'])
    # download(res1['thumburl'], "./data/emoji/", res1['md5'], True)
    print(get_emoji(xml_string, True))
    print(get_emoji(xml_string, False))
#     http://vweixinf.tc.qq.com/110/20403/stodownload?m=3a4d439aba02dce4834b2c54e9f15597&filekey=3043020101042f302d02016e0402534804203361346434333961626130326463653438333462326335346539663135353937020213f0040d00000004627466730000000131&hy=SH&storeid=323032313037323030373236313130303039653236646365316535316534383236386234306230303030303036653033303034666233&ef=3&bizid=1022
