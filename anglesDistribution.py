#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 18 10:57:49 2018

@author: ngritti
"""

import numpy as np
import glob
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


#%%
def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0), (0, 1))
            1.5707963267948966
            >>> angle_between((1, 0), (1, 0))
            0.0
            >>> angle_between((1, 0), (-1, 0))
            3.141592653589793
    """
    dot = np.dot(v1,v2)
    det = v1[0]*v2[1]-v1[1]*v2[0]
    return np.arctan2(det,dot)

def vector(p1,p2):
    return p2-p1

#%%

class tethers(object):
    
    def __init__(self, basedir):
        self.basedir = basedir
        self.fList = glob.glob(basedir+'/*.txt'); self.fList.sort()
        self.chamber_idx = self.get_ch_idx()
        self.xyz_pos = self.read_files()
        self.zt_pos = self.extract_angles()
        
    #%% Load data
        
    def get_ch_idx(self):
        chidx = {}
        for chn in ['Atrium','Ventricle','AVCanal']:
            try:
                chidx[chn] = ['_'+chn+'.txt' in f for f in self.fList].index(True)
            except:
                continue
        assert 'AVCanal' in chidx.keys(), 'No AVCanal file! Can\'t continue analysis!'
        print('#'*40)
        print('I found the following files:')
        for chn in chidx:
            print('   ' + self.fList[chidx[chn]])
        print('#'*40)
        return chidx
    
    def read_files(self):
        
        points = {}
        for chn in self.chamber_idx.keys():
            i = self.chamber_idx[chn]
            tmp = []
            with open(self.fList[i]) as f:
                lines = f.readlines()
                for l in lines:
                    v=np.array(l.split(",")).astype(np.float32)
                    tmp.append(v)
            tmp = np.array(tmp)
            points[chn] = tmp
        
        return points
    
    #%% extract angles
    
    def extract_angles(self):
        zt_pos = {}
        refs = self.xyz_pos['AVCanal']
        for chn in [x for x in self.chamber_idx.keys() if x != 'AVCanal']:
            tethers = self.xyz_pos[chn]
            data = []
            if chn == 'Ventricle':
                vref = vector(refs[2,:2],refs[1,:2])
            elif chn == 'Atrium':
                vref = vector(refs[0,:2],refs[1,:2])
            for t in tethers:
                if chn == 'Ventricle':
                    vtet = vector(refs[2,:2],t[:2])
                elif chn == 'Atrium':
                    vtet = vector(refs[0,:2],t[:2])
                theta = angle_between(vref,vtet)*180/np.pi
                data.append([t[2],theta])
            zt_pos[chn] = np.array(data)
        return zt_pos
    
    
    #%% Plot data
    
    def plot_XY(self, chambers=['Atrium','Ventricle'],
                xlim=(0,1000), ylim=(0,1000),
                alpha=0.5, ms=6, marker='o'):
        if isinstance(chambers,str): chambers = [chambers]
        chamber_names = list(self.chamber_idx.keys())
        assert all([ch in chamber_names for ch in chambers]), 'Can\'t recognize the chamber!'
        assert 'AVCanal' not in chambers, 'AVCanal is not a chamber!'

        plt.figure(figsize=(5,5))
        plt.subplots_adjust(top=0.95,right=0.95)
        refs = self.xyz_pos['AVCanal']
        lines=[]
        for chn in chambers:
            tethers = self.xyz_pos[chn]
            if chn=='Atrium':
                plt.plot(refs[:2,0],refs[:2,1],'-r',lw=2)
                color = 'red'
            elif chn=='Ventricle':
                plt.plot(refs[1:,0],refs[1:,1],'-g',lw=2)
                color = 'green'
            l,=plt.plot(tethers[:,0],tethers[:,1],marker, ms=ms, mew=0.,
                        color=color, alpha=alpha,
                        label=chn)
            lines.append(l)
        plt.xlim(xlim)
        plt.ylim(ylim)
        plt.legend(handles=lines)

        # plt.show()
    
    def plot_XYZ(self, chambers=['Atrium','Ventricle'],
                xlim=(0,1000), ylim=(0,1000),
                alpha=0.5, ms=6):
        fig = plt.figure(figsize=(5,5))
        plt.subplots_adjust(left=0.05,bottom=0.05,right=0.95,top=0.95)
        ax = fig.add_subplot(111, projection='3d')

        refs = self.xyz_pos['AVCanal']
        lines=[]
        for chn in chambers:
            tethers = self.xyz_pos[chn]
            if chn=='Atrium':
                ax.plot(refs[:2,0],refs[:2,1],refs[:2,2],'-r',lw=2)
                color = 'red'
            elif chn=='Ventricle':
                ax.plot(refs[1:,0],refs[1:,1],refs[1:,2],'-g',lw=2)
                color = 'green'
            l,=ax.plot(tethers[:,0],tethers[:,1],tethers[:,2],
                           'o', ms=ms, mew=0.,
                           color=color, alpha=alpha,
                           label=chn)
            lines.append(l)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.legend(handles=lines)
        

    def plot_ZT(self, chambers=['Atrium','Ventricle'],
                marker='|'):
        if isinstance(chambers,str): chambers = [chambers]
        for ch in chambers:
            self.plot_ZT_singleChamber(ch,marker=marker)

    def plot_ZT_singleChamber(self, chamber,
                              marker='|'):
        chamber_names = list(self.chamber_idx.keys())
        assert chamber in chamber_names, 'Can\'t recognize the chamber!'
        assert chamber != 'AVCanal', 'AVCanal is not a chamber!'

        plt.figure(figsize=(5,2.5))
        plt.subplots_adjust(bottom=0.2,right=0.99)
        plt.xticks([-180,-135,-90,-45,0,45,90,135,180])
        data = self.zt_pos[chamber]
        ymax = 50
        zs = np.linspace(0,ymax,int(ymax/5)+1) # horizontal lines on the angles plot
        for z in zs:
           plt.plot([-180,180],[z,z],'--k',lw=0.25)
        plt.plot([0,0],[np.min(zs),np.max(zs)],'-b',lw=1)
        color = 'red' if chamber == 'Atrium' else 'green'
        plt.plot(data[:,1],data[:,0],marker, color=color)
        plt.title(chamber)
        plt.ylabel('Z slice')
        plt.xlabel('Angle')
        plt.ylim([0,ymax]) # set limits on the vertical axis
        # plt.show()

    #%%
    
    def save_angles_data(self):
        outfile = self.fList[self.chamber_idx['AVCanal']].split('AVCanal')[0]
        for chn in [x for x in self.chamber_idx.keys() if x != 'AVCanal']:
            np.savetxt(outfile+'angles'+chn+'.txt',self.zt_pos[chn])

'''
The only input needed
'''
paths = [ '180907_kdrlrasCherry_myl7radGFP_001_merged',
    '180907_kdrlrasCherry_myl7radGFP_002_merged',
    '180914_kdrlrasCherry_mylGFP_ZO1_3_merge',
    '180914_kdrlrasCherry_mylGFP_ZO1_4_merge_good',
    '180928_kdrlrasCherry_myl7rasGFP_paxillin_2_merge_good',
    '180928_kdrlrasCherry_myl7rasGFP_paxillin_3_merge_good',
    '180928_kdrlrasCherry_myl7rasGFP_paxillin_4_merge_good',
    '181107_kdrlRasCherry_Myl7GFP_phalloidine647_003_merge/try1',
    '181107_kdrlRasCherry_Myl7GFP_phalloidine647_003_merge/try2',
    '181107_kdrlRasCherry_Myl7GFP_phalloidine647_001_merge/try1',
    '181107_kdrlRasCherry_Myl7GFP_phalloidine647_001_merge/try2_better',
    ]

path = paths[3]
### load data
data = tethers(path)

### plot and save data
data.plot_XY(chambers=['Atrium','Ventricle'])
data.plot_ZT(chambers='Atrium')
# data.plot_ZT(chambers='Ventricle')
data.plot_XYZ()
# data.save_angles_data()
#
plt.show()