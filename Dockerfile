# This Dockerfile constructs a docker image that contains an installation
# of jupyter, neuropythy, and various dependencies of these.
#
# Example build:
#   docker build --no-cache --tag nben/hcp-lines `pwd`
# (but really, use docker-compose up instead).
#

# Start with the Ubuntu for now
FROM nben/neuropythy:latest

# Note the Maintainer.
MAINTAINER Noah C. Benson <nben@nyu.edu>

# Copy over some files...
COPY ./npythyrc /home/$NB_USER/.npythyrc
COPY hcp_lines /home/$NBUSER/.pypath/hcp_line
ENV PYTHONPATH=/home/$NBUSER/.pypath

