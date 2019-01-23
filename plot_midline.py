#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  7 15:51:21 2019
@author: ngritti
"""

import numpy as np
#import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from tqdm import tqdm
from time import time
import glob, os, sys

def compute_rot_mat(d,th):
    ct = np.cos(th)
    st = np.sin(th)
    ct_d = 1-ct
    r1 = np.array( [ ct+d[0]*d[0]*ct_d, d[0]*d[1]*ct_d-d[2]*st, d[0]*d[2]*ct_d+d[1]*st ] )
    r2 = np.array( [ d[0]*d[1]*ct_d+d[2]*st, ct+d[1]*d[1]*ct_d, d[1]*d[2]*ct_d-d[0]*st ] )
    r3 = np.array( [ d[0]*d[2]*ct_d-d[1]*st, d[1]*d[2]*ct_d+d[0]*st, ct+d[2]*d[2]*ct_d ] )
    return np.stack([r1,r2,r3])

class Midline(object):
    
    def __init__(self, coords_file):
        self.coords_file = coords_file
        self.pxlsize = [0.41, 0.41, 2.]
        self.coords_anchors, self.n_points = self.read_file()
        
    def read_file(self):
        coords_anchors = []

        with open(self.coords_file) as f:
            lines = f.readlines()
            i=0
            for l in lines:
                try:
                    params = np.array( [np.float(v) for v in l.split(",")] )
                    params *= self.pxlsize
                    i += 1
                    # save value as an integer
                    coords_anchors.append(params)
                except ValueError:
                    pass
        coords_anchors = np.array(coords_anchors)
        n_coords = coords_anchors.shape[0]
        print('#'*40)
        print('N coords:', n_coords)
        print('#'*40)
        
        return coords_anchors, n_coords
    
    #%%
    def fix_outliers(self, idx = -1, thr = 2.):
        # first, fix angles
        for i in range(self.coords_anchors.shape[0]-1):
            if np.abs(self.coords_anchors[i+1,2] - self.coords_anchors[i,2])>90:
                self.coords_anchors[i+1,2] -= 180
        
        if idx == -1:
            diff = np.sqrt(np.diff(self.coords_anchors[:,0])**2+np.diff(self.coords_anchors[:,1])**2)
        else:
            diff = np.abs(np.diff(self.coords_anchors[:,idx]))
        diff_mean = np.mean(diff)
        print(diff.shape)
        for i in range(self.n_coords-1):
            if diff[i]>(thr*diff_mean):
                print(i, diff[i],diff_mean)
                for j in range(self.coords_anchors.shape[1]):
                    self.coords_anchors[i+1,j] = (self.coords_anchors[i,j]+self.coords_anchors[i+2,j])/2
                diff = np.abs(np.diff(self.coords_anchors[:,idx]))

    def smooth_midline(self,sigma=5):
        from scipy.ndimage import gaussian_filter1d
        for i in range(self.coords_anchors.shape[1]):
            self.coords_anchors[:,i] = gaussian_filter1d(self.coords_anchors[:,i], sigma)

    #%% 
    def setup_figure(self, figsize=(10,5),viewpoint=(45,60),
        axoff = True):

        fig = plt.figure(figsize=figsize)
        plt.subplots_adjust(left=0.,bottom=0.,right=1.,top=1.)
        plt.style.use('dark_background')
        ax = fig.add_subplot(111, projection='3d')

        if axoff:
            ax.grid(False)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_zticks([])
            ax.set_axis_off() 
        ax.set_xlim([0,450])
        ax.set_ylim([-50,250])
        ax.set_zlim([200,500])
        ax.view_init(*viewpoint)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        
        return fig, ax

    def extract_midline_coord_system(self,
                    plot = True, figsize = (10,5), viewpoint=(30,60), vect_length=10, n_vect_show=20, axoff=True,
                    smooth_order = 100, interp_order=3, method= 'pt'):
        assert(method in ['fs','pt']), 'Invalid method!'
        centroid = np.copy(self.coords_anchors)
        # print(centroid.shape)
        
        # # spline interpolation
        from scipy import interpolate
        tck, u = interpolate.splprep(np.transpose(centroid), s=smooth_order, k=interp_order)
        # first, compute a very fine spline
        u_fine = np.linspace(0,1.,10000)
        z_fine, y_fine, x_fine = interpolate.splev(u_fine, tck)
        S = np.transpose( np.array( [z_fine,y_fine,x_fine] ) )
        spline_length = np.sum(np.linalg.norm(np.diff(S,axis=0),axis=1))
        print('Spline length with %d points: %.3f'%(10000, spline_length) )
        n_points_spline = int(spline_length)
        # then, compute the spline only on the right amount of points, i.e. such that they are homogeneously spaced 1pxl
        u_fine = np.linspace(0,1.,n_points_spline)
        z_fine, y_fine, x_fine = interpolate.splev(u_fine, tck)
        S = np.transpose( np.array( [z_fine,y_fine,x_fine] ) )
        
        # Compute all tangents 
        T = np.gradient(S,edge_order=2,axis=0)
        T = np.array( [ t/np.linalg.norm(t) for t in T ] )

        if method == 'fs': # frenet-serret frame
            N = np.gradient(T,edge_order=2,axis=0)
            N = np.array( [ n/np.linalg.norm(n) for n in N ] )

        elif method == 'pt': # parallel-transported frame, based on https://janakiev.com/blog/framing-parametric-curves/
            N = np.gradient(T,edge_order=2,axis=0)
            N = np.array( [ n/np.linalg.norm(n) for n in N ] )
            for i in range(n_points_spline - 1):
                b = np.cross(T[i], T[i + 1]) # compute cross product of consecutive tangents
                b = b / np.linalg.norm(b) # normalize vectore
                phi = np.arccos(np.dot(T[i], T[i + 1])) # compute angle between consecutive tangent
                R = compute_rot_mat(b,phi) # compute 3D rotation matrix
                N[i + 1] = np.dot(R, N[i]) # rotate previous N and save it as current N
                
        # Calculate the second normal vector B
        B = np.array([np.cross(t, n) for (t, n) in zip(T, N)])

        # plot everything
        if plot:
            fig, ax = self.setup_figure(figsize,viewpoint,axoff=axoff)
            show_step = int(n_points_spline/n_vect_show)
            ax.plot(centroid[:,0],centroid[:,1],centroid[:,2],'o',color='white',alpha=.3,ms=3)
            ax.plot(S[:,0],S[:,1],S[:,2],'-',color='white',lw=2,alpha=.6)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                T[::show_step,0],T[::show_step,1],T[::show_step,2],
                color='g',length=10,lw=1)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                N[::show_step,0],N[::show_step,1],N[::show_step,2],
                color='b',length=10,lw=1)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                B[::show_step,0],B[::show_step,1],B[::show_step,2],
                color='r',length=10,lw=1)

        # check if vectors are hortogonal and unitary
        # for t,n,b in zip(T,N,B):
        #     print('(t,n), (n,b), (t,b) angles: ',np.sum(t*n),np.sum(b*n),np.sum(t*b))
        #     print('t,n,b lengths: ',np.sum(t*t),np.sum(n*n),np.sum(b*b))

        # plt.show()
        return n_points_spline, S, T, N, B


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

class Tethers(object):
    
    def __init__(self, basedir):
        self.pxlsize = [0.41, 0.41, 2.]
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
            points[chn] = tmp*self.pxlsize
        
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
                alpha=0.5, ms=6,
                plot_midline = False, midline=[],method='pt'):
        fig = plt.figure(figsize=(5,5))
        plt.subplots_adjust(left=0.05,bottom=0.05,right=0.95,top=0.95)
        ax = fig.add_subplot(111, projection='3d')

        refs = self.xyz_pos['AVCanal']
        lines=[]
        for chn in chambers:
            tethers = self.xyz_pos[chn]
            if chn=='Atrium':
                color = '#1f77b4'
                # ax.plot(refs[:2,0],refs[:2,1],refs[:2,2],'-',color=color,lw=2)
            elif chn=='Ventricle':
                color = '#ff7f0e'
                # ax.plot(refs[1:,0],refs[1:,1],refs[1:,2],'-',color=color,lw=2)
                
            l,=ax.plot(tethers[:,0],tethers[:,1],tethers[:,2],
                           'o', ms=ms, mew=0.,
                           color=color, alpha=alpha,
                           label=chn)
            lines.append(l)
        if plot_midline:
            n_points_spline,S,T,N,B = midline.extract_midline_coord_system(smooth_order=100, plot=False, method=method)
            show_step = int(n_points_spline/10)
            ax.plot(S[:,0],S[:,1],S[:,2],'-',color='black',lw=2,alpha=.6)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                T[::show_step,0],T[::show_step,1],T[::show_step,2],
                color='g',length=5,lw=1)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                N[::show_step,0],N[::show_step,1],N[::show_step,2],
                color='b',length=5,lw=1)
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
        color = 'orange' if chamber == 'Atrium' else 'blue'
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

    def project_tethers(self,midline,smooth_order=100,method='pt'):
        n_points_spline,S,T,N,B = midline.extract_midline_coord_system(smooth_order=smooth_order, plot=False, method=method)
        t = np.linspace(0,1,n_points_spline)

        t_pos = {}
        angles = {}
        plt.figure()
        colors={'Atrium':'#1f77b4','Ventricle':'#ff7f0e'}
        for chamber in ['Atrium','Ventricle']:
            t_pos[chamber] = []
            angles[chamber] = []
            for tether in self.xyz_pos[chamber]:
                # print(tether)
                dist = [np.linalg.norm(tether-m) for m in S]
                i = np.where(dist==np.min(dist))[0][0]
                t_pos[chamber].append(t[i])
                angles[chamber].append(angle_between(tether-S[i],N[i])*180/np.pi)
            l,=plt.plot(angles[chamber],t_pos[chamber],'o',color=colors[chamber],ms=2)

        # find AVCanal position
        dist = [np.linalg.norm(self.xyz_pos['AVCanal'][1,:]-m) for m in S]
        i = np.where(dist==np.min(dist))[0][0]
        avcanal = t[i]
        plt.plot([-180,180],[avcanal,avcanal],'-k')

        plt.legend(['Atrium','Ventricle','AVCanal'], loc='upper right', fontsize=7)
        plt.xlabel('Angle')
        plt.ylabel('Distance along the midline')


'''
The only input needed
'''
# paths = [ '180907_kdrlrasCherry_myl7radGFP_001_merged',
#     '180907_kdrlrasCherry_myl7radGFP_002_merged',
#     '180914_kdrlrasCherry_mylGFP_ZO1_3_merge',
#     '180914_kdrlrasCherry_mylGFP_ZO1_4_merge_good',
#     '180928_kdrlrasCherry_myl7rasGFP_paxillin_2_merge_good',
#     '180928_kdrlrasCherry_myl7rasGFP_paxillin_3_merge_good',
#     '180928_kdrlrasCherry_myl7rasGFP_paxillin_4_merge_good',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_003_merge/try1',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_003_merge/try2',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_001_merge/try1',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_001_merge/try2_better',
#     ]

# path = paths[3]

midline = Midline('test_unwrap_heart/midline_49.txt')
# midline.fix_outliers(idx=3)
# midline.smooth_tube(sigma=5)

method = 'pt'
tethers = Tethers('test_unwrap_heart')
tethers.project_tethers(midline, method=method)
tethers.plot_XYZ(xlim=(100,300),ylim=(0,200),plot_midline=True,midline=midline,method=method)

plt.show()

