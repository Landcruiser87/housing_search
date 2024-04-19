import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import datetime
import time
import support


import requests

cookies = {
    'ads_prefs': '"HBERAAA="',
    'auth_token': '5bb021e3a82ed3dd3ac7ce36080427cb13e75de0',
    'twid': 'u%3D253625430',
    'guest_id': 'v1%3A166652788531472405',
    'guest_id_ads': 'v1%3A166652788531472405',
    'guest_id_marketing': 'v1%3A166652788531472405',
    'lang': 'en',
    'ct0': 'c20c3c02b154de6f8f54a6291a55be870b097aed052a67e13c8aaa097fbb7aef212ba56046b18648d470d5a5eb8e15e94573e7e40904485dd4520d6b0dec6bcdf092795631b3f5f8243e3a6c05097e1e',
    'external_referer': 'padhuUp37zjgzgv1mFWxJ12Ozwit7owX|0|8e8t2xd8A2w%3D',
    '_ga': 'GA1.2.889301126.1693492354',
    '_gid': 'GA1.2.446430375.1693492354',
    'personalization_id': '"v1_5b3avHlv5RCDQCbcR5g35w=="',
}

headers = {
    'authority': 'twitter.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    # 'cookie': 'ads_prefs="HBERAAA="; auth_token=5bb021e3a82ed3dd3ac7ce36080427cb13e75de0; twid=u%3D253625430; guest_id=v1%3A166652788531472405; guest_id_ads=v1%3A166652788531472405; guest_id_marketing=v1%3A166652788531472405; lang=en; ct0=c20c3c02b154de6f8f54a6291a55be870b097aed052a67e13c8aaa097fbb7aef212ba56046b18648d470d5a5eb8e15e94573e7e40904485dd4520d6b0dec6bcdf092795631b3f5f8243e3a6c05097e1e; external_referer=padhuUp37zjgzgv1mFWxJ12Ozwit7owX|0|8e8t2xd8A2w%3D; _ga=GA1.2.889301126.1693492354; _gid=GA1.2.446430375.1693492354; personalization_id="v1_5b3avHlv5RCDQCbcR5g35w=="',
    'pragma': 'no-cache',
    'referer': 'https://twitter.com/AndrewYNg',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'x-client-transaction-id': 'WwdqX5M7I19PZGYl0zkSSwteQ/dWX5L9Ml/bM3twvYPCpb65p7BfmQ9RuLzradobN2gQ+lu2ojoXlUzPhX+6iRqgSMTLWg',
    'x-client-uuid': '21b399c7-43b4-42a5-8e1a-5d4042beeab6',
    'x-csrf-token': 'c20c3c02b154de6f8f54a6291a55be870b097aed052a67e13c8aaa097fbb7aef212ba56046b18648d470d5a5eb8e15e94573e7e40904485dd4520d6b0dec6bcdf092795631b3f5f8243e3a6c05097e1e',
    'x-twitter-active-user': 'yes',
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
}

params = {
    'variables': '{"userId":"216939636","count":20,"includePromotedContent":true,"withQuickPromoteEligibilityTweetFields":true,"withVoice":true,"withV2Timeline":true}',
    'features': '{"rweb_lists_timeline_redesign_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}',
}

response = requests.get(
    'https://twitter.com/i/api/graphql/XicnWRbyQ3WgVY__VataBQ/UserTweets',
    params=params,
    cookies=cookies,
    headers=headers,
)

#Just in case we piss someone off
if response.status_code != 200:
	print(f'Status code: {response.status_code}')
	print(f'Reason: {response.reason}')
	exit()
else:
	print(f'You\'re ok!!! Status code:{response.status_code}')

#Grab the Json Data
resp_json = response.json()



resp_json["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"][2]["entries"]

for x in range(29):
	resp_json["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"][2]["entries"][x]["content"]["itemContent"]["tweet_results"]["result"]["note_tweet"]["note_tweet_results"]["result"]["text"]