FROM python:3.12-slim

ARG WORKDIR=/app
ARG USERNAME=python
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt-get update  \
    && export DEBIAN_FRONTEND=noninteractive \
    #
    # installl selenium requirements 
    && apt-get install -y --no-install-recommends git \
    #
	# add non-root user
	&& groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/zsh --uid $USER_UID --gid $USER_GID -m $USERNAME \
	#
    # clean-up
    && apt-get autoremove -y  \
    && apt-get clean -y  \
    && rm -rf /var/lib/apt/lists/* /tmp/library-scripts

# install pipenv
RUN pip --disable-pip-version-check --no-cache-dir install pipenv

# create project dir  
RUN mkdir $WORKDIR

# copy files
COPY . $WORKDIR

# change current working dir to project dir
WORKDIR $WORKDIR

# install project deps
RUN pipenv install --system --deploy --ignore-pipfile

# own files
RUN chown -R $USERNAME:$USERNAME $WORKDIR

# run script
CMD [ "/usr/local/bin/python3", "/app/script.py" ]
