FROM amfraenkel/android-malware-project

USER root

COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt  && \
	fix-permissions $CONDA_DIR

RUN apt-get install -y htop

RUN conda update pandas -y \
	&& conda clean -afy && fix-permissions $CONDA_DIR
