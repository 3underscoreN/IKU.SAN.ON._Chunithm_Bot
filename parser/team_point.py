from bs4 import BeautifulSoup
from parser.navigator import Navigator

import json
from dotenv import dotenv_values

from collections import OrderedDict
from typing import Optional

import logging

with open('parser/cfg.json', 'r', encoding='utf-8') as cfg_file:
  user_cfg = json.load(cfg_file)

CHUNITHM_NET_ENGLISH_URL = user_cfg.get('CHUNITHM_NET_ENGLISH_URL_BASE', 'https://chunithm-net-eng.com/mobile')
TEAM_MEMBER_URL = f'{CHUNITHM_NET_ENGLISH_URL}/team/teamMember'

logger = logging.getLogger(__name__)

env_cfg = dotenv_values()

async def get_team_scores() -> OrderedDict[str, int]:
  """
  Launches a Playwright browser to log into the Chunithm Net English website,
  navigates to the team member page, and retrieves the team scores.

  Please note that in order to mimic human behavior and avoid bot detection, this function includes random wait times between actions. 
  It is a good idea to run this command in an async function.

  :return: An ordered dictionary mapping player names to their scores.
  :rtype: OrderedDict[str, int]

  :raises ValueError: If SEGA ID or password (`PARSER_SEGA_ID`, `PARSER_SEGA_PW`) is not found in environment variables.
  :raises Exception: If there is an error during the login or navigation process.
  """
  async with Navigator(TEAM_MEMBER_URL) as page:
    # obtain html content
    html_content = await page.content()

    # parsing team scores
    logger.info('Parsing team scores from HTML content...')
    team_scores = _parse_team_scores(html_content)

    return team_scores

def _parse_team_scores(html: str) -> OrderedDict[str, int]:
  """
  Parses the HTML content of the team member page to extract player names and their scores.
  
  :param html: HTML content of the CHUNITHM team member page.
  :type html: str
  :return: An ordered dictionary mapping player names to their scores.
  :rtype: OrderedDict[str, int]
  """

  player_scores = OrderedDict()

  def player_scores_locator(classname: Optional[str]) -> bool:
    if classname:
      player_box_classes = [
        'team_member_profile_box_1st',
        'team_member_profile_box_2nd',
        'team_member_profile_box_3rd',
        'team_member_profile_box_normal'
      ]

      if classname in player_box_classes:
        return True
      
    return False

  soup = BeautifulSoup(html, 'html.parser')

  # maximum 20 players in 1 group
  player_divs = soup.find_all('div', class_=player_scores_locator, recursive=True, limit=20)
  
  # this is sorted by appearance order on the page.
  # Since SEGA already sorts the values for us, it is sorted as long order is maintained.
  for player_div in player_divs:
    name: str = 'Unknown'
    score: int = 0        # preset values

    name_div = player_div.find('div', class_='player_name_in')

    if name_div:
      name = name_div.get_text(strip=True)

    label_div = player_div.find('div', string=lambda text: text and 'This month\'s earned point' in text.strip()) #type: ignore
    if label_div:
      score_div = label_div.find_next_sibling('div')
      if score_div:
        score_text = score_div.get_text(strip=True).replace(',', '')
        try:
          score = int(score_text)
        except ValueError:
          score = 0

    if name != 'Unknown':
      player_scores[name] = score

  return player_scores