package com.binus.ootd;

import android.app.Application;
import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import androidx.recyclerview.widget.RecyclerView;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class CalenderAdaptor extends RecyclerView.Adapter<CalenderAdaptor.CalenderViewHolder> {
    private ArrayList<LocalDate> daysofMonth;
    private OnItemListener onItemListener;
    private String uid;

    private FirebaseDatabase rootNode;
    private DatabaseReference taskReference;
    private FirebaseAuth mAuth;

    private LocalDate date;

    public CalenderAdaptor(ArrayList<LocalDate> daysofMonth, String uid, OnItemListener onItemListener, Application mApplication) {
        this.daysofMonth = daysofMonth;
        this.uid = uid;
        this.onItemListener = onItemListener;

        rootNode = FirebaseDatabase.getInstance();
        mAuth = FirebaseAuth.getInstance();

        taskReference = rootNode.getReference("tasks").child(mAuth.getUid());
    }

    @NonNull
    @Override
    public CalenderViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        View view = inflater.inflate(R.layout.calender_cell,parent,false);
        ViewGroup.LayoutParams layoutparams = view.getLayoutParams();
        layoutparams.height = (int)(parent.getHeight() * 0.166666);
        return new CalenderViewHolder(daysofMonth, onItemListener, view);
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    @Override
    public void onBindViewHolder(@NonNull CalenderViewHolder holder, int position) {
        final LocalDate date = daysofMonth.get(position);

        if(date == null)
            holder.dayofMonth.setText("");
        else{
            holder.dayofMonth.setText(String.valueOf(date.getDayOfMonth()));
            if(date.equals(YourTaskActivity.selectedDate))
                holder.parentView.setBackgroundResource(R.drawable.calendar_bg);

            ValueEventListener postListener = new ValueEventListener() {
                @Override
                public void onDataChange(DataSnapshot dataSnapshot) {
                    Iterable<DataSnapshot> taskList = dataSnapshot.getChildren();

                    for(DataSnapshot task:taskList) {
                        if(date.toString().equals(task.getKey())){
                            holder.dayofMonth.setTextColor(Color.rgb(255,89 , 0));
                        }
                    }
                }

                @Override
                public void onCancelled(DatabaseError databaseError) {

                }
            };
            taskReference.addValueEventListener(postListener);
        }
    }

    @Override
    public int getItemCount() {
        return daysofMonth.size();
    }

    public interface OnItemListener{
        void onItemClick(int position,LocalDate date);
    }


    public class CalenderViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener{
        private final ArrayList<LocalDate> daysofMonth;
        public final View parentView;
        public final CalenderAdaptor.OnItemListener onItemListener;
        public final TextView dayofMonth;

        public CalenderViewHolder(ArrayList<LocalDate> daysofMonth, OnItemListener onItemListener, @NonNull View itemView) {
            super(itemView);
            this.daysofMonth = daysofMonth;
            parentView = itemView.findViewById(R.id.parentView);
            this.onItemListener = onItemListener;
            dayofMonth = itemView.findViewById(R.id.cellday);
            itemView.setOnClickListener(this);
        }

        @Override
        public void onClick(View view) {
            onItemListener.onItemClick(getAdapterPosition(),daysofMonth.get(getAdapterPosition()));
        }
    }
}
