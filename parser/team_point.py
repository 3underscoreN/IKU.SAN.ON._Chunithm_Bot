from playwright.async_api import async_playwright, expect
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

import asyncio

import random

import os

from dotenv import dotenv_values

from bs4 import BeautifulSoup

from collections import OrderedDict

from typing import Optional

import logging

STATE_FILE = '_parser_state.json'

CHUNITHM_NET_ENGLISH_URL = 'https://chunithm-net-eng.com/mobile'
TEAM_MEMBER_URL = f'{CHUNITHM_NET_ENGLISH_URL}/team/teamMember'
ERROR_URL = f'{CHUNITHM_NET_ENGLISH_URL}/error'
HOME_URL = f'{CHUNITHM_NET_ENGLISH_URL}/home'

logger = logging.getLogger(__name__)

cfg = dotenv_values()

async def _wait_random(min_seconds: float, max_seconds: float) -> None:
  """
  Simply a function that waits for a random amount of time specified.

  :param min_seconds: Minimum number of seconds to wait.
  :param max_seconds: Maximum number of seconds to wait.
  :type min_seconds: float
  :type max_seconds: float

  :return: None
  :rtype: None
  """
  wait_time = random.uniform(min_seconds, max_seconds)
  logger.debug(f'Waiting for {wait_time:.2f} seconds to mimic human behavior.')
  await asyncio.sleep(wait_time)

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

  # Determine if a state file exists
  is_state_file_exists = False
  if os.path.exists(STATE_FILE):
    is_state_file_exists = True

  username: Optional[str] = cfg.get('PARSER_SEGA_ID')
  password: Optional[str] = cfg.get('PARSER_SEGA_PW')

  if not username or not password:
    raise ValueError('SEGA ID or password not found in environment variables.')
  
  async with async_playwright() as ap:

    browser = await ap.chromium.launch(headless=True)
    context = await browser.new_context(storage_state=STATE_FILE if is_state_file_exists else None)
    page = await context.new_page()
    # Navigate to the team member page
    await page.goto(TEAM_MEMBER_URL)
    await page.wait_for_load_state("networkidle", timeout=60000)

    # navigate to team member page again if error
    if page.url.startswith(ERROR_URL):
      
      logger.info('Encountered CHUNITHM error page. Going back...')
      await _wait_random(0.5, 1.2)
      await page.locator('div.btn_back').click()

      try:
        await page.wait_for_load_state("networkidle", timeout=10000)
      except PlaywrightTimeoutError:
        # sometimes loading gets stuck for whatever reason, so we retry 1 time here
        logger.warning('Timeout while waiting for page to load after going back from error page. Retrying...')
        await page.reload(timeout=60000, wait_until="networkidle")
      if page.url.startswith(HOME_URL):
        logger.info('Returned to home page successfully.')

      else:
        logger.info('Not logged in, proceeding to login...')

        # tick agree to terms
        await _wait_random(0.5, 1.1)
        await page.get_by_role("checkbox", name="Agree to the terms of use for").check()
        await _wait_random(1.4, 2.5)

        await page.locator('span.c-button--openid--segaId').click()
        await asyncio.sleep(2)

        # enter id and pw
        sega_id_textbox = page.locator('input#sid')
        await sega_id_textbox.fill(username)
        await _wait_random(2.5, 3.8)
        sega_pw_textbox = page.locator('input#password')
        await sega_pw_textbox.fill(password)
        await _wait_random(2.7, 4.0)

        await page.locator('button#btnSubmit').click()

        logger.info('Login submitted.')
        await _wait_random(0.5, 1.2)

        # Check if login was successful by verifying the URL
        try:
          expect(page.locator('li.btn_team')).to_be_visible(timeout=15000)
          logger.info('Login successful, navigating to team member page.')
        except PlaywrightTimeoutError:
          raise Exception('Login failed or took too long. Please check your SEGA ID and password.')

      # navigate to team member page again
      await page.locator('li.btn_team').click()
      await _wait_random(0.4, 1.0)
      await page.locator('li.submenu_member').click()

      # Ensure the team member profile boxes are visible
      await asyncio.sleep(2)

    # obtain html content
    html_content = await page.content()

    # parsing team scores
    logger.info('Parsing team scores from HTML content...')

    team_scores = _parse_team_scores(html_content)

    # save storage state
    await context.storage_state(path=STATE_FILE)
    await browser.close()
    logger.debug('Browser for team point parsing closed; state saved.')

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
  
  for player_div in player_divs:
    name: str = 'Unknown'
    score: int = 0        # preset values

    name_div = player_div.find('div', class_='player_name_in')

    if name_div:
      name = name_div.get_text(strip=True)

    label_div = player_div.find('div', string=lambda text: text and 'This month\'s earned point' in text.strip())
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