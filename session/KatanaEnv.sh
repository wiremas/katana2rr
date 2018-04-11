#!/bin/bash
#Katana Environment file

# TODO - solve this!!!
# export PROJECTSHARE=/bigfoot/tearsinheaven/
# export PIPELINEPATH=/bigfoor/tearsinheaven/PIPELINE/

# arnold env
export ARNOLD_PLUGIN_PATH=$ARNOLD_PLUGIN_PATH:/opt/alShaders/
export ARNOLD_SHADERLIB_PATH=$ARNOLD_SHADERLIB_PATH:/opt/alShaders/bin/

# prman env
# export RFKTREE=/opt/pixar/RenderManForKatana-21.0-katana2.1
# export RMSTREE=$RFKTREE
# export KATANA_RESOURCES=$KATANA_RESOURCES:/home/MEDIANET/aschachner/Documents/work/tools/katana2rr_local/
# export RMANFB=/opt/pixar/RenderManForKatana-21.0-katana2.2/bin/
# export RMAN_RIXPLUGINPATH=/opt/pixar/RenderManProServer-21.0/lib/plugins/
# export RMAN_RIXPLUGINPATH=${RMANTREE}/lib/RIS/pattern:${RMANTREE}/lib/RIS/bxdf:${RMANTREE}/lib/RIS/integrator:${RMANTREE}/lib/RIS/light:${RMANTREE}/lib/RIS/projection
# export RMAN_SHADERPATH=/opt/pixar/RenderManProServer-21.0/lib/shaders/



# projectroot
# export PROJECTSHARE=/home/MEDIANET/$USER/mnt/tearsinheaven
export PROJECTSHARE=/bigfoot/tearsinheaven/
# pipelineroot
export PIPELINEPATH=$PROJECTSHARE/PIPELINE
# local path to the rrSubmitter katana plugin
export KATANAPLUGINDIR=/home/MEDIANET/aschachner/Documents/work/tools/katana2rr/ # $PIPELINEPATH/software/Katana/Resources/
# renderman root
export PXRINSTALLDIR=/opt/pixar

# --------------------------------------------------------------------------------- #
# RenderMan / Katana
# --------------------------------------------------------------------------------- #

export RMANTREE=$PXRINSTALLDIR/RenderManProServer-21.0
export RMAN_RIXPLUGINPATH=$PXRINSTALLDIR/RenderManProServer-21.0/lib/plugins/
export RMAN_SHADERPATH=$PXRINSTALLDIR/RenderManProServer-21.0/lib/shaders/
export KATANA_RESOURCES=$KATANA_RESOURCES:$PXRINSTALLDIR/RenderManForKatana.21.0-katana2.1/plugins/Resources/PRMan21:$KATANAPLUGINDIR
