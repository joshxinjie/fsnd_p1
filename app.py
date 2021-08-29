#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import render_template, request, Response, flash, redirect, url_for
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import Venue, Artist, Show, app, db


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  """
  Retrieves venues data from the database.

  Example of areas data:
  data=[{
    "city": "San Francisco",
    "state": "CA",
    "venues": [{
      "id": 1,
      "name": "The Musical Hop",
      "num_upcoming_shows": 0,
    }, {
      "id": 3,
      "name": "Park Square Live Music & Coffee",
      "num_upcoming_shows": 1,
    }]
  }, {
    "city": "New York",
    "state": "NY",
    "venues": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }]

  Parameters
  ----------
  None

  Returns
  -------
  data: list[dict]
    Venue data from the database.
  """

  data = []

  city_state_results = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  city_venues_result_list = []
  for city_state in city_state_results:
    city, state = city_state[0], city_state[1]
    venues = db.session.query(Venue)\
      .filter(Venue.city == city)\
      .filter(Venue.state == state)\
      .all()
    venues_result_list = []
    for venue in venues:
      venue_id = venue.id
      venue_name = venue.name
      num_upcoming_shows = search_num_upcoming_shows_by_venue(venue_id)
      venues_result_list.append({
        "id": venue_id,
        "name": venue_name,
        "num_upcoming_shows": num_upcoming_shows
      })
    data.append({
      "city": city,
      "state": state,
      "venues": venues_result_list
    })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  """
  Performs search on venues with partial string search. Search is case-insensitive.
  Seach for Hop should return "The Musical Hop".
  Search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  Example of response:
  {
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }

  Parameters
  ----------
  None

  Returns
  -------
  response: dict
    The search results.
  """

  data = []

  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  results_counts = len(search_results)

  for result in search_results:
    venue_id = result.id
    venue_name = result.name
    num_upcoming_shows = search_num_upcoming_shows_by_venue(venue_id)
    data.append({
      "id": venue_id,
      "name": venue_name,
      "num_upcoming_shows": num_upcoming_shows
    })

  response = {
    "count": results_counts,
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

def search_num_upcoming_shows_by_venue(venue_id):
  """
  Searches for the number of upcoming shows to be hosted at the specified venue.

  Parameters
  ----------
  venue_id : int
    The venue ID in the database.

  Returns
  -------
  int
    The number of upcoming shows to be hosted at the specified venue.
  """
  search_results = db.session.query(Show)\
    .filter(Show.venue_id == venue_id)\
    .filter(Show.start_time > datetime.now())\
    .all()

  return len(search_results)

def search_num_past_shows_by_venue(venue_id):
  """
  Searches for the number of past shows to be hosted at the specified venue.

  Parameters
  ----------
  venue_id : int
    The venue ID in the database.

  Returns
  -------
  int
    The number of past shows to be hosted at the specified venue.
  """
  search_results = db.session.query(Show)\
    .filter(Show.venue_id == venue_id)\
    .filter(Show.start_time <= datetime.now())\
    .all()

  return len(search_results)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  """
  Shows the venue page with the given venue_id.

  Example of venue_data
  {
    "id": 6,
    "name": "Park Square Live Music & Coffee",
    "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
    "address": "34 Whiskey Moore Ave",
    "city": "San Francisco",
    "state": "CA",
    "phone": "415-000-1234",
    "website": "https://www.parksquarelivemusicandcoffee.com",
    "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
    "seeking_talent": False,
    "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    "past_shows": [{
      "artist_id": 5,
      "artist_name": "Matt Quevedo",
      "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [{
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 1,
    "upcoming_shows_count": 1,
  }

  Parameters
  ----------
  venue_id : int
    The venue ID in the database.
  
  Returns
  -------
  venue_data: dict
    Data associated with the venue with the given venue_id.
  """
  
  venue_data = db.session.query(
      Venue.id,\
      Venue.name,\
      Venue.genres,\
      Venue.address,\
      Venue.city,\
      Venue.state,\
      Venue.phone,\
      Venue.website_link,\
      Venue.facebook_link,\
      Venue.seeking_talent,\
      Venue.seeking_description,\
      Venue.image_link
    ).filter(Venue.id == venue_id).all()[0]

  id, name, genres, address, city, state, phone, website_link, facebook_link, seeking_talent, seeking_description, image_link =\
    venue_data[0], venue_data[1], venue_data[2], venue_data[3], venue_data[4], venue_data[5], venue_data[6], venue_data[7], venue_data[8], venue_data[9], venue_data[10], venue_data[11]

  past_shows = find_past_shows_by_venue(id)
  upcoming_shows = find_upcoming_shows_by_venue(id)
  past_shows_count = len(past_shows)
  upcoming_shows_count = len(upcoming_shows)

  venue_data = {
    "id": id,
    "name": name,
    "genres": genres,
    "address": address,
    "city": city,
    "state": state,
    "phone": phone,
    "website_link": website_link,
    "facebook_link": facebook_link,
    "seeking_talent": seeking_talent,
    "seeking_description": seeking_description,
    "image_link": image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count
  }

  return render_template('pages/show_venue.html', venue=venue_data)

def find_past_shows_by_venue(venue_id):
  """
  Retreives all past shows hosted at the venue with the given venue ID.
  
  Example of past_show_list:
  [{
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }]

  Parameters
  ----------
  venue_id : int
    The venue ID in the database.
  
  Returns
  -------
  past_show_list: list[dict]
    The past shows data.
  """
  past_show_list = []
  past_shows_at_venue = db.session.query(
    Show.artist_id,\
    Artist.name,\
    Artist.image_link,\
    Show.start_time,\
    Show
  )\
  .join(Artist, Show.artist_id == Artist.id)\
  .filter(Show.venue_id == venue_id)\
  .filter(Show.start_time <= datetime.now())\
  .all()
  for past_show in past_shows_at_venue:
    artist_id, artist_name, artist_image_link, start_time = past_show[0], past_show[1], past_show[2], past_show[3]
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    past_show_list.append({
      "artist_id": artist_id,
      "artist_name": artist_name,
      "artist_image_link": artist_image_link,
      "start_time": start_time
    })
  return past_show_list

def find_upcoming_shows_by_venue(venue_id):
  """
  Retreives all upcoming shows to be hosted at the venue with the given venue ID.
  
  Example of upcoming_show_list:
  [{
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
  }]

  Parameters
  ----------
  venue_id : int
    The venue ID in the database.
  
  Returns
  -------
  upcoming_show_list: list[dict]
    The upcoming shows data.
  """

  upcoming_show_list = []
  upcoming_shows_at_venue = db.session.query(
    Show.artist_id,\
    Artist.name,\
    Artist.image_link,\
    Show.start_time,\
    Show
  )\
  .join(Artist, Show.artist_id == Artist.id)\
  .filter(Show.venue_id == venue_id)\
  .filter(Show.start_time > datetime.now())\
  .all()
  for upcoming_show in upcoming_shows_at_venue:
    artist_id, artist_name, artist_image_link, start_time = upcoming_show[0], upcoming_show[1], upcoming_show[2], upcoming_show[3]
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    upcoming_show_list.append({
      "artist_id": artist_id,
      "artist_name": artist_name,
      "artist_image_link": artist_image_link,
      "start_time": start_time
    })
  return upcoming_show_list

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  """
  Insert form data as a new Venue record in the database.

  Parameters
  ----------
  None

  Returns
  -------
  None
  """

  error = False
  try:
    seeking_talent = False
    seeking_description = ''
    if 'seeking_talent' in request.form:
      seeking_talent = request.form['seeking_talent'] == 'y'
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']
    new_venue = Venue(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      genres = request.form.getlist('genres'),
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_talent = seeking_talent,
      seeking_description = seeking_description
    )
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  """
  Endpoint that takes a venue_id, and uses SQLAlchemy ORM to delete a record.

  Parameters
  ----------
  venue_id: int
    The venue ID in the database.

  Returns
  -------
  None
  """

  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully deleted!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be deleted.')
    print(sys.exc_info())
  finally:
    db.session.close()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  """
  Retrieves all artists IDs and names in the database.

  Example of artists data:
  artists = [{
              "id": 4,
              "name": "Guns N Petals",
            }, {
              "id": 5,
              "name": "Matt Quevedo",
            }, {
              "id": 6,
              "name": "The Wild Sax Band",
            }]

  Parameters
  ----------
  None

  Returns
  -------
  artists: list[dict]
    All artists IDs and names.
  """

  artists_results = db.session.query(Artist.id, Artist.name)\
    .group_by(Artist.id, Artist.name)\
    .order_by(Artist.id)\
    .all()
  
  return render_template('pages/artists.html', artists=artists_results)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  """
  Performs search on artists with partial string search. Ensure it is case-insensitive.
  Seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  Search for "band" should return "The Wild Sax Band".

  Example of response:
  {
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }

  Parameters
  ----------
  None

  Returns
  -------
  response: dict
    The artists search results.
  """

  data = []

  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  results_counts = len(search_results)

  for result in search_results:
    artist_id = result.id
    artist_name = result.name
    num_upcoming_shows = search_num_upcoming_shows_by_artist(artist_id)
    data.append({
      "id": artist_id,
      "name": artist_name,
      "num_upcoming_shows": num_upcoming_shows
    })

  response = {
    "count": results_counts,
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

def search_num_upcoming_shows_by_artist(artist_id):
  """
  Searches for the number of upcoming shows to be perform by the specified artist.

  Parameters
  ----------
  artist_id : int
    The artist id.

  Returns
  -------
  int
    The number of upcoming shows to be performed by the artist.
  """
  search_results = db.session.query(Show)\
    .filter(Show.artist_id == artist_id)\
    .filter(Show.start_time > datetime.now())\
    .all()

  return len(search_results)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  """
  Shows the artist page with the given artist_id.

  Example of artist_data:
  {
    "id": 1,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "past_shows": [{
      "venue_id": 4,
      "venue_name": "The Musical Hop",
      "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }

  Parameters
  ----------
  artist_id : int
    The artist id.

  Returns
  -------
  artist_data: dict
    The artist data associated with the given artist ID.
  """

  artist_data = db.session.query(
    Artist.id,\
    Artist.name,\
    Artist.genres,\
    Artist.city,\
    Artist.state,\
    Artist.phone,\
    Artist.facebook_link,\
    Artist.seeking_venue,\
    Artist.seeking_description,\
    Artist.image_link,\
    Artist.website_link,\
  ).filter(Artist.id == artist_id).all()[0]

  id, name, genres, city, state, phone, facebook_link, seeking_venue, seeking_description, image_link, website_link =\
    artist_data[0], artist_data[1], artist_data[2], artist_data[3], artist_data[4], artist_data[5], artist_data[6], artist_data[7], artist_data[8], artist_data[9], artist_data[10]

  past_shows = find_past_shows_by_artist(id)
  upcoming_shows = find_upcoming_shows_by_artist(id)
  past_shows_count = len(past_shows)
  upcoming_shows_count = len(upcoming_shows)

  artist_data = {
    "id": id,
    "name": name,
    "genres": genres,
    "city": city,
    "state": state,
    "phone": phone,
    "facebook_link": facebook_link,
    "seeking_venue": seeking_venue,
    "seeking_description": seeking_description,
    "image_link": image_link,
    "website_link": website_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count
  }

  return render_template('pages/show_artist.html', artist=artist_data)

def find_past_shows_by_artist(artist_id):
  """
  Retrieves all past shows by the artist with the given artist_id.

  Example of past_show_list:
  [{
    "venue_id": 4,
    "venue_name": "The Musical Hop",
    "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    "start_time": "2019-05-21T21:30:00.000Z"
  }]

  Parameters
  ----------
  artist_id : int
    The artist id.

  Returns
  -------
  past_show_list: list[dict]
    The past shows data.
  """
  past_show_list = []

  past_shows_by_artist = db.session.query(
    Show.venue_id,\
    Venue.name,\
    Venue.image_link,\
    Show.start_time,\
    Show
  )\
  .join(Venue, Show.venue_id == Venue.id)\
  .filter(Show.artist_id == artist_id)\
  .filter(Show.start_time <= datetime.now())\
  .all()

  for past_show in past_shows_by_artist:
    venue_id, venue_name, venue_image_link, start_time = past_show[0], past_show[1], past_show[2], past_show[3]
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    past_show_list.append({
      "venue_id": venue_id,
      "venue_name": venue_name,
      "venue_image_link": venue_image_link,
      "start_time": start_time
    })
  return past_show_list

def find_upcoming_shows_by_artist(artist_id):
  """
  Retrieves all upcoming shows by the artist with the given artist_id.

  Parameters
  ----------
  artist_id : int
    The artist id.

  Returns
  -------
  upcoming_show_list: list[dict]
    The upcoming shows data.
  """
  upcoming_show_list = []

  upcoming_shows_by_artist = db.session.query(
    Show.venue_id,\
    Venue.name,\
    Venue.image_link,\
    Show.start_time,\
    Show
  )\
  .join(Venue, Show.venue_id == Venue.id)\
  .filter(Show.artist_id == artist_id)\
  .filter(Show.start_time > datetime.now())\
  .all()

  for upcoming_show in upcoming_shows_by_artist:
    venue_id, venue_name, venue_image_link, start_time = upcoming_show[0], upcoming_show[1], upcoming_show[2], upcoming_show[3]
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    upcoming_show_list.append({
      "venue_id": venue_id,
      "venue_name": venue_name,
      "venue_image_link": venue_image_link,
      "start_time": start_time
    })
  return upcoming_show_list

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  """
  Retrieves the artist information with the given artist ID from the database, 
  and populate the fields in the edit artist form.

  Parameters
  ----------
  artist_id : int
    The artist id.

  Returns
  -------
  None
  """
  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  if artist:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  """
  Retrieves the edited artist information from the submitted form and updates 
  the existing artist record with ID <artist_id> using the new attributes.

  Parameters
  ----------
  artist_id : int
    The artist id.

  Returns
  -------
  None
  """

  error = False
  artist = Artist.query.get(artist_id)

  try:
    seeking_venue = False
    seeking_description = ''
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']
    
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = seeking_venue
    artist.seeking_description = seeking_description
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  """
  Retrieves the venue information with the given venue ID from the database, 
  and populate the fields in the edit venue form.

  Parameters
  ----------
  venue_id : int
    The venue id.

  Returns
  -------
  None
  """
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue:
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  """
  Retrieves the edited venue information from the submitted form and updates 
  the existing venue record with ID <venue_id> using the new attributes.

  Parameters
  ----------
  venue_id : int
    The venue id.

  Returns
  -------
  None
  """
  error = False
  venue = Venue.query.get(venue_id)

  try:
    seeking_talent = False
    seeking_description = ''
    if 'seeking_talent' in request.form:
      seeking_talent = request.form['seeking_talent'] == 'y'
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']
    
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website_link = request.form['website_link']
    venue.seeking_talent = seeking_talent
    venue.seeking_description = seeking_description
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  """
  Insert form data as a new Artist record in the database.
  
  Parameters
  ----------
  None

  Returns
  -------
  None
  """
  error = False
  try:
    seeking_venue = False
    seeking_description = ''
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']
    new_artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      genres = request.form.getlist('genres'),
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_venue = seeking_venue,
      seeking_description = seeking_description
    )
    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  """
  Displays list of shows at /shows

  Example of show_data:
  [{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }]

  Parameters
  ----------
  None

  Returns
  -------
  show_data: list[dict]
    The shows data recorded in the database.
  """

  show_data = []

  show_results = db.session.query(Show.venue_id, Venue.name, Show.artist_id, Artist.name, Artist.image_link, Show.start_time, Show)\
    .join(Venue, Show.venue_id == Venue.id)\
    .join(Artist, Show.artist_id == Artist.id)\
    .all()

  for show in show_results:
    venue_id, venue_name, artist_id, artist_name, artist_image_link, start_time = show[0], show[1], show[2], show[3], show[4], show[5]
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    show_data.append({
      "venue_id": venue_id,
      "venue_name": venue_name,
      "artist_id": artist_id,
      "artist_name": artist_name,
      "artist_image_link": artist_image_link,
      "start_time": start_time
    })
  
  return render_template('pages/shows.html', shows=show_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  """
  Insert form data as a new Show record in the database.
  
  Parameters
  ----------
  None

  Returns
  -------
  None
  """
  error = False
  try:
    new_show = Show(
      venue_id = request.form['venue_id'],
      artist_id = request.form['artist_id'],
      start_time = request.form['start_time']
    )
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
