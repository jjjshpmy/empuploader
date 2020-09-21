VIRTUAL_ENV=$(dirname "$(dirname "$(which python)")")
mkdir -p ${VIRTUAL_ENV}/tmp
pushd ${VIRTUAL_ENV}/tmp
if [ `uname -s` = "Darwin" ]; then
  CHROMEDRIVER_ARCH=mac64
  CHROME_EXE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
  CHROMEDRIVER_ARCH=linux64
  CHROME_EXE=google-chrome
fi
CHROME_MAJOR_VERSION=`"${CHROME_EXE}" --version | awk '{print $NF}' | cut -d. -f1`
CHROMEDRIVER_VERSION=`curl https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}`
wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_${CHROMEDRIVER_ARCH}.zip
unzip chromedriver_${CHROMEDRIVER_ARCH}.zip
mv chromedriver ${VIRTUAL_ENV}/bin/
rm -Rf ${VIRTUAL_ENV}/tmp
popd
